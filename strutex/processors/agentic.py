"""
Agentic Processor - Autonomous extraction using LangGraph.
"""

import json
import logging
import os
import hashlib
import threading
import asyncio
import html
from typing import Any, Dict, List, Optional, Type, Union, TypedDict, Annotated, Set
import operator

# Internal imports
from .base import Processor
from .simple import SimpleProcessor
from .rag import RagProcessor
from .sequential import SequentialProcessor
from ..types import Schema
from ..documents import get_mime_type

# Conditional imports for optional dependencies
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Constants (Control Rods)
MAX_HISTORY_LENGTH = 50
MAX_ITERATIONS = 5
MAX_REPETITION_COUNT = 2
MAX_TOOL_CALL_LENGTH = 1000 # Safety limit for hashed keys
MAX_RERANK_RESULTS = 3

logger = logging.getLogger("strutex.processors.agentic")


def history_reducer(left: List[Dict[str, Any]], right: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Strictly cap history size to prevent context/memory bloat (Containment)."""
    full = left + right
    if len(full) > MAX_HISTORY_LENGTH:
        return full[-MAX_HISTORY_LENGTH:]
    return full


class AgentState(TypedDict):
    """State for the AgenticProcessor loop."""
    input_file: str
    prompt: str
    schema: Optional[Schema]
    history: Annotated[List[Dict[str, Any]], history_reducer]
    intermediate_data: Dict[str, Any]
    ingested_files: Set[str]
    tool_counts: Dict[str, int]
    next_step: str
    completed: bool
    final_result: Optional[Any]
    error: Optional[str] # Unified error signal


class AgenticProcessor(Processor):
    """
    Autonomous extraction processor using LangGraph.
    
    This processor does not follow a fixed path. It uses an LLM to 'plan'
    which tools (other processors or search) to use based on the document
    content and the target schema.
    """
    
    def __init__(
        self,
        max_iterations: int = MAX_ITERATIONS,
        **kwargs
    ):
        """
        Args:
            max_iterations: Maximum number of agent steps.
            **kwargs: Shared configuration (provider, model, etc.).
        """
        super().__init__(**kwargs)
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "langgraph is not installed. Please install it with: "
                "pip install langgraph"
            )
        self.max_iterations = max_iterations
        self._lock = threading.RLock()
        self._rag_cache = None # Optimization: Cache RagProcessor instance
        
        # Define tool registry for extensible execution
        self._tools = {
            "get_metadata": {
                "func": self._tool_get_metadata,
                "desc": "get_metadata(): Returns file size and mime type."
            },
            "count_pages": {
                "func": self._tool_count_pages,
                "desc": "count_pages(): Returns total pages (PDF) or 1."
            },
            "scan_page": {
                "func": self._tool_scan_page,
                "desc": "scan_page(prompt): Extracts text/data from the file based on prompt."
            },
            "semantic_search": {
                "func": self._tool_semantic_search,
                "desc": "semantic_search(query, top_k=5): Search for facts. Returns observation and is_relevant flag."
            },
            "rewrite_query": {
                "func": self._tool_rewrite_query,
                "desc": "rewrite_query(query): Transforms a failed query into technical variations to improve search."
            },
            "verify_grounding": {
                "func": self._tool_verify_grounding,
                "desc": "verify_grounding(extraction, sources): Checks if extraction is supported by documents to avoid hallucinations."
            },
            "rerank": {
                "func": self._tool_rerank,
                "desc": "rerank(observations, criteria): Filters and ranks the top 3 most relevant facts from a list."
            },
            "summarizer": {
                "func": self._tool_summarizer,
                "desc": "summarizer(): Returns a high-level summary of the document content."
            },
            "sequential_scan": {
                "func": self._tool_sequential_scan,
                "desc": "sequential_scan(prompt): Reads the document segment by segment for high-fidelity extraction."
            }
        }
        
        self._graph = self._build_graph()

    def _get_rag(self) -> RagProcessor:
        """Lazy-init and cache RAG processor for efficiency (Optimization)."""
        if self._rag_cache is None:
            self._rag_cache = RagProcessor(**self._config)
        return self._rag_cache

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        builder = StateGraph(AgentState)
        
        builder.add_node("planner", self._planner_node)
        builder.add_node("actor", self._actor_node)
        builder.add_node("finalizer", self._finalizer_node)
        
        builder.set_entry_point("planner")
        
        builder.add_conditional_edges(
            "planner",
            self._should_continue,
            {
                "continue": "actor",
                "end": "finalizer"
            }
        )
        
        builder.add_edge("actor", "planner")
        builder.add_edge("finalizer", END)
        
        return builder.compile()

    async def _planner_node(self, state: AgentState) -> Dict[str, Any]:
        """Decide the next action based on current state."""
        tool_descriptions = "\n".join([t["desc"] for t in self._tools.values()])
        format_instructions = (
            "You must return ONLY a JSON object with this structure:\n"
            '{"thought": "reasoning here", "tool": "tool_name", "args": {"arg1": "val1"}}\n'
            f"Available tools:\n{tool_descriptions}\n"
            "finish(): Use when you have all the data required by the schema.\n"
            "Corrective RAG Strategy:\n"
            "1. If 'semantic_search' returns 'is_relevant': False, DO NOT proceed with it. Use 'rewrite_query' or 'sequential_scan'.\n"
            "2. Always use 'verify_grounding' on your final extraction set before calling 'finish()'.\n"
            "3. If search fails repeatedly, use 'summarizer' to get a high-level view of the document."
        )
        
        # Security: Enhanced prompt sanitization (Containment)
        # Using html.escape to prevent more complex injection attacks
        goal = html.escape(state['prompt']).replace("{", "[").replace("}", "]")
        
        prompt = (
            f"Extraction Goal: {goal}\n"
            f"Target Schema: {state['schema']}\n"
            f"Data gathered so far: {json.dumps(state['intermediate_data'], indent=2)}\n"
            f"History: {json.dumps(state['history'][-5:], indent=2)}\n\n"
            f"{format_instructions}"
        )
        
        try:
            plan_raw = await self._provider.aprocess(
                file_path=state['input_file'],
                prompt=prompt,
                schema=None, 
                mime_type="text/plain"
            )
            
            plan_data = plan_raw if isinstance(plan_raw, dict) else self._parse_json(str(plan_raw))
            tool = plan_data.get("tool", "finish").lower()
            
            if tool == "finish":
                return {"next_step": "finish", "completed": True}
                
            history_update = [{"role": "planner", "content": plan_data.get("thought", "Acting...")}]
            
            return {
                "next_step": json.dumps(plan_data), 
                "history": history_update
            }
        except Exception as e:
            logger.error(f"Agentic Planner failed: {e}")
            return {"completed": True, "next_step": "error", "error": str(e)}

    async def _actor_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute the tool selected by the planner."""
        try:
            plan_data = json.loads(state["next_step"])
            tool_name = plan_data.get("tool", "").lower()
            args = plan_data.get("args", {})
            
            logger.info(f"Agent executing tool: {tool_name}")
            
            if tool_name not in self._tools:
                return {"history": [{"role": "actor", "content": f"Unknown tool: {tool_name}"}]}

            # Execute tool from registry
            tool_func = self._tools[tool_name]["func"]
            result, state_updates = await tool_func(state, args)
            
            # Automated Correction Loop: Validate observation
            validation_error = self._validate_step_result(result, state["schema"])
            if validation_error:
                logger.warning(f"Validation Error caught in Actor: {validation_error}")
                return {
                    "history": [{"role": "actor", "content": f"Correction required for {tool_name}: {validation_error}"}],
                    "error": None # Reset error so planner can try again with this feedback
                }
            
            # Loop detection (Hashed Keys for safety)
            args_json = json.dumps(args, sort_keys=True)
            args_hash = hashlib.md5(args_json.encode()).hexdigest()
            new_key = f"{tool_name}:{args_hash}"
            
            new_counts = state["tool_counts"].copy()
            new_counts[new_key] = new_counts.get(new_key, 0) + 1
            
            # Merge results into intermediate data
            new_data = state["intermediate_data"].copy()
            if isinstance(result, dict):
                new_data.update(result)
            else:
                new_data[f"obs_{len(state['history'])}"] = str(result)
                
            updates = {
                "intermediate_data": new_data,
                "tool_counts": new_counts,
                "history": [{"role": "actor", "content": f"Used {tool_name}: {str(result)[:100]}..."}]
            }
            if state_updates:
                updates.update(state_updates)
            return updates
            
        except Exception as e:
            logger.error(f"Agentic Actor failed: {e}")
            return {
                "history": [{"role": "actor", "content": f"Tool failed: {e}"}],
                "error": str(e)
            }

    # --- Tool Implementations ---

    async def _tool_get_metadata(self, state: AgentState, args: Dict[str, Any]) -> Any:
        if "mime_type" in state["intermediate_data"] and "file_size" in state["intermediate_data"]:
            return {
                "mime_type": state["intermediate_data"]["mime_type"],
                "file_size": state["intermediate_data"]["file_size"]
            }, {}
            
        result = {
            "mime_type": get_mime_type(state['input_file']), 
            "file_size": os.path.getsize(state['input_file'])
        }
        return result, {}

    async def _tool_count_pages(self, state: AgentState, args: Dict[str, Any]) -> Any:
        if "page_count" in state["intermediate_data"]:
            return {"page_count": state["intermediate_data"]["page_count"]}, {}

        mime = get_mime_type(state['input_file'])
        if "pdf" in mime and PYPDF_AVAILABLE:
            reader = PdfReader(state['input_file'])
            result = {"page_count": len(reader.pages)}
        else:
            result = {"page_count": 1}
        return result, {}

    async def _tool_scan_page(self, state: AgentState, args: Dict[str, Any]) -> Any:
        result = await self._provider.aprocess(
            file_path=state['input_file'],
            prompt=args.get("prompt", "Extract relevant data"),
            schema=None,
            mime_type="text/plain"
        )
        return result, {}

    async def _tool_semantic_search(self, state: AgentState, args: Dict[str, Any]) -> Any:
        rag = self._get_rag()
        state_updates = {}
        
        # Performance: Optimization to avoid redundant ingestion
        if state['input_file'] not in state['ingested_files']:
            logger.info(f"RAG Ingesting {state['input_file']} for the first time in this session.")
            # Ingest is currently sync, run in thread
            await asyncio.to_thread(rag.ingest, state['input_file'])
            state_updates["ingested_files"] = state["ingested_files"] | {state["input_file"]}
        
        result = await rag.aquery(args.get("query", ""), top_k=args.get("top_k", 5))
        
        # Relevance Grader (Agentic Core)
        check_prompt = (
            f"Extraction Objective: {state['prompt']}\n"
            f"Search Results: {json.dumps(result)}\n\n"
            "Does this data contain enough specific information to help fulfill the objective? Respond strictly with 'YES' or 'NO'."
        )
        relevance_raw = await self._provider.aprocess(
            file_path=state['input_file'],
            prompt=check_prompt,
            schema=None,
            mime_type="text/plain"
        )
        is_relevant = "YES" in str(relevance_raw).upper()
        
        return {
            "observation": result,
            "is_relevant": is_relevant,
            "query_used": args.get("query")
        }, state_updates

    async def _tool_rewrite_query(self, state: AgentState, args: Dict[str, Any]) -> Any:
        query = args.get("query", "")
        prompt = (
            f"Original Query: {query}\n"
            "The search yielded no relevant results. Rewrite this query into 3 distinct, technical, or broader "
            "search strings that might find the information in a business/technical document. "
            "Return a JSON list of strings."
        )
        variations = await self._provider.aprocess(
            file_path=state['input_file'],
            prompt=prompt,
            schema=None,
            mime_type="text/plain"
        )
        # Parse if string, otherwise return as is
        expanded = variations if isinstance(variations, list) else self._parse_json(str(variations))
        return {"expanded_queries": expanded}, {}

    async def _tool_verify_grounding(self, state: AgentState, args: Dict[str, Any]) -> Any:
        extraction = args.get("extraction", {})
        sources = args.get("sources", state["intermediate_data"])
        
        prompt = (
            f"Extraction to verify: {json.dumps(extraction)}\n"
            f"Available evidence: {json.dumps(sources)}\n\n"
            "Is every claim in the extraction strictly supported by the evidence? "
            "Return a JSON object: {'supported': True, 'hallucinations': []}"
        )
        result = await self._provider.aprocess(
            file_path=state['input_file'],
            prompt=prompt,
            schema=None,
            mime_type="text/plain"
        )
        return {"grounding_check": result}, {}

    async def _tool_rerank(self, state: AgentState, args: Dict[str, Any]) -> Any:
        observations = args.get("observations", [])
        criteria = args.get("criteria", "Relevance to extraction goal")
        
        if not observations:
            return {"error": "No observations provided to rerank"}, {}
            
        prompt = (
            f"Given these facts: {json.dumps(observations)}\n"
            f"Rank and select the top 3 that best satisfy: {criteria}.\n"
            "Return only the selected items as a JSON list."
        )
        
        result = await self._provider.aprocess(
            file_path=state['input_file'],
            prompt=prompt,
            schema=None,
            mime_type="text/plain"
        )
        return {"reranked_results": result}, {}

    async def _tool_summarizer(self, state: AgentState, args: Dict[str, Any]) -> Any:
        result = await self._provider.aprocess(
            file_path=state['input_file'],
            prompt="Summarize the key contents of this document elegantly focusing on entities and main facts.",
            schema=None,
            mime_type="text/plain"
        )
        return result, {}

    async def _tool_sequential_scan(self, state: AgentState, args: Dict[str, Any]) -> Any:
        seq = SequentialProcessor(**self._config)
        result = await seq.aprocess(
            state['input_file'],
            args.get("prompt", state["prompt"]),
            schema=None
        )
        return result, {}

    # --- Utils ---

    def _validate_step_result(self, result: Any, schema: Optional[Schema]) -> Optional[str]:
        """Check if the tool output is fundamentally flawed for the target schema."""
        if not schema or not isinstance(result, dict):
            return None
            
        # Check for obvious type mismatches if provided in result keys
        # This is a heuristic check to trigger the correction loop
        for key, val in result.items():
            if key in schema.properties:
                from ..plugins.plugin_type import PluginType # Avoid circulars or use property
                prop_type = type(schema.properties[key]).__name__.lower()
                if "string" in prop_type and not isinstance(val, str):
                    return f"Type mismatch for '{key}': expected string, got {type(val).__name__}"
                if "integer" in prop_type and not isinstance(val, (int, float)):
                    # Allow float if it can be int, but if it's alphanumeric text, it's an error
                    if isinstance(val, str) and not val.isdigit():
                        return f"Type mismatch for '{key}': expected number, got non-numeric string '{val}'"
        return None

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Robustly extract JSON from LLM text."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
        return {"tool": "finish"}

    async def _finalizer_node(self, state: AgentState) -> Dict[str, Any]:
        """Produce the final structured result."""
        if state.get("error") and not state["intermediate_data"]:
            return {"final_result": {"error": f"Agent failed prematurely: {state.get('error')}"}}

        result = await self._provider.aprocess(
            file_path=state['input_file'],
            prompt=f"Synthesize this gathered info into the final schema.\nGathered data: {json.dumps(state['intermediate_data'])}",
            schema=state['schema'],
            mime_type="text/plain"
        )
        return {"final_result": result}

    def _should_continue(self, state: AgentState) -> str:
        """Route based on completion status and loop detection."""
        if state.get("completed") or state.get("error"):
            return "end"
            
        # Hard limits
        if len(state["history"]) > self.max_iterations * 2:
            logger.warning(f"Agent reached max iterations ({self.max_iterations}).")
            return "end"
            
        # Loop detection (Containment)
        for tool_call, count in state.get("tool_counts", {}).items():
            if count > MAX_REPETITION_COUNT:
                logger.warning(f"Loop detected for tool call: {tool_call}. Terminating.")
                return "end"
                
        return "continue"

    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        **kwargs
    ) -> Any:
        # Sync bridge for aprocess

        # Use the current event loop if it exists, otherwise create a new one.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If the loop is already running (e.g., in a Jupyter notebook or nested async),
            # we run it in a separate thread.
            res = [None]
            err = [None]
            def _thread_target():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    res[0] = new_loop.run_until_complete(
                        self.aprocess(file_path, prompt, schema, model, **kwargs)
                    )
                except Exception as e:
                    err[0] = e
            t = threading.Thread(target=_thread_target)
            t.start()
            t.join()
            if err[0]:
                raise err[0]
            return res[0]
        else:
            return loop.run_until_complete(
                self.aprocess(file_path, prompt, schema, model, **kwargs)
            )

    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        **kwargs
    ) -> Any:
        # Pydantic conversion
        pydantic_schema, pydantic_model = self._convert_pydantic(model)
        if pydantic_schema:
            schema = pydantic_schema
            
        initial_state = {
            "input_file": file_path,
            "prompt": prompt,
            "schema": schema,
            "history": [],
            "intermediate_data": {},
            "ingested_files": set(),
            "tool_counts": {},
            "next_step": "",
            "completed": False,
            "final_result": None,
            "error": None
        }
        
        # Lock is still good to have even in async if multiple concurrent 
        # calls target the same graph instance (though graph.ainvoke is re-entrant).
        # However, LangGraph invoke handles state isolation per-call. 
        # The lock here protects shared resources in the processor instance if any.
        async with asyncio.Lock(): # Replacing threading.RLock with async lock for consistency
            final_state = await self._graph.ainvoke(initial_state)
            
        result = final_state["final_result"]
        
        return self._validate_pydantic(result, pydantic_model)
