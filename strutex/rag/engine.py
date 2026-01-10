"""
RAG Engine for strutex.
Orchestrates the RAG workflow using LangGraph.
"""
from typing import List, Dict, Any, Optional, TypedDict
import json

try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from .vectorstore import QdrantVectorStore


class RagState(TypedDict):
    """State for the RAG graph."""
    query: str
    context_docs: List[Dict[str, Any]]
    answer: Optional[str]
    schema: Optional[Any]  # strutex.types.Schema
    schema_instructions: str
    collection_name: Optional[str]
    top_k: int


class RagEngine:
    """
    Engine that orchestrates the RAG flow.
    
    Uses LangGraph to define a flexible pipeline for:
    Retrieval -> Context Augmentation -> Generation
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore,
        processor: Any,  # DocumentProcessor instance
    ):
        """
        Initialize the RAG engine.
        
        Args:
            vector_store: Vector store for retrieval.
            processor: DocumentProcessor instance for extraction.
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "langgraph is not installed. Please install it with: "
                "pip install 'strutex[rag]'"
            )
            
        self.vector_store = vector_store
        self.processor = processor
        self.graph = self._build_graph()

    def _build_graph(self) -> "StateGraph":
        """Build the LangGraph for RAG."""
        workflow = StateGraph(RagState)

        # Define nodes
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("generate", self._generate_node)

        # Define edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    def _retrieve_node(self, state: RagState) -> Dict[str, Any]:
        """Node for retrieving relevant documents."""
        docs = self.vector_store.search(
            query=state["query"],
            collection_name=state.get("collection_name"),
            limit=state.get("top_k", 5)
        )
        return {"context_docs": docs}

    def _generate_node(self, state: RagState) -> Dict[str, Any]:
        """Node for generating structured extraction from context."""
        context_text = "\n\n".join([d["content"] for d in state["context_docs"]])
        
        # We use the processor's _extract_from_text method (to be added)
        # to perform structured extraction from the synthesized context.
        try:
            result = self.processor._extract_from_text(
                text=context_text,
                prompt=state["query"],
                schema=state.get("schema"),
                schema_instructions=state["schema_instructions"]
            )
            return {"answer": result}
        except Exception as e:
            # Fallback or error handling
            return {"answer": f"Error during generation: {str(e)}"}

    def query(
        self, 
        query: str, 
        schema_instructions: str = "",
        collection_name: Optional[str] = None,
        schema: Optional[Any] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Run the RAG query.
        
        Args:
            query: User query.
            schema_instructions: Instructions for structured output.
            
        Returns:
            Extracted result.
        """
        initial_state = {
            "query": query,
            "context_docs": [],
            "answer": None,
            "schema": schema,
            "schema_instructions": schema_instructions,
            "collection_name": collection_name,
            "top_k": top_k
        }
        
    async def aquery(
        self, 
        query: str, 
        schema_instructions: str = "",
        collection_name: Optional[str] = None,
        schema: Optional[Any] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Run the RAG query asynchronously.
        """
        initial_state = {
            "query": query,
            "context_docs": [],
            "answer": None,
            "schema": schema,
            "schema_instructions": schema_instructions,
            "collection_name": collection_name,
            "top_k": top_k
        }
        
        return await self.graph.ainvoke(initial_state)
