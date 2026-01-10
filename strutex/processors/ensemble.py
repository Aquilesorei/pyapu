"""
Ensemble processor - combines results from multiple providers using a judge.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union

from .base import Processor
from .simple import SimpleProcessor

logger = logging.getLogger("strutex.processors.ensemble")

class EnsembleProcessor(Processor):
    """
    Processor that calls multiple providers and synthesizes the results.
    
    Uses a 'judge' provider to review all outputs and produce the final result.
    
    Example:
        >>> ensemble = EnsembleProcessor(
        ...     providers=[openai_proc, gemini_proc],
        ...     judge=expensive_proc
        ... )
    """
    
    def __init__(
        self,
        providers: List[Processor],
        judge: Optional[Processor] = None,
        synthesis_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Args:
            providers: List of Processor instances to query.
            judge: Processor used to synthesize the results. 
                  If None, the first provider in the list is used as judge.
            synthesis_prompt: Custom prompt for the judge.
            **kwargs: Shared configuration.
        """
        super().__init__(**kwargs)
        self._providers = providers
        self._judge = judge or providers[0]
        self._synthesis_prompt = synthesis_prompt or (
            "You are an expert data validator. Below are multiple extraction results "
            "from the same document by different models. Your task is to review them, "
            "resolve any contradictions, and provide the most accurate final JSON result "
            "following the requested schema.\n\n"
            "Results:\n{results}"
        )

    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        all_results = []
        for i, provider_input in enumerate(self._providers):
            try:
                # If provider is a string or config dict, create a processor for it
                if isinstance(provider_input, (str, dict)):
                    from .simple import SimpleProcessor
                    if isinstance(provider_input, str):
                        processor = SimpleProcessor(provider=provider_input)
                    else:
                        processor = SimpleProcessor(**provider_input)
                else:
                    processor = provider_input

                res = processor.process(file_path, prompt, schema=schema, model=model, **kwargs)
                all_results.append({
                    "provider": processor._provider.__class__.__name__ if hasattr(processor, '_provider') else f"Model {i+1}",
                    "result": res
                })
            except Exception as e:
                logger.warning(f"Ensemble member {i+1} failed: {e}")
                
        if not all_results:
            raise RuntimeError("All ensemble members failed")
            
        # 2. If only one result, return it (no need for judge)
        if len(all_results) == 1:
            return all_results[0]["result"]
            
        # 3. Synthesize with judge
        results_str = json.dumps(all_results, indent=2)
        judge_prompt = self._synthesis_prompt.format(results=results_str)
        
        logger.info(f"Synthesizing {len(all_results)} results using judge")
        
        # Ensure judge is a processor
        judge_processor = self._judge
        if isinstance(judge_processor, (str, dict)):
            from .simple import SimpleProcessor
            if isinstance(judge_processor, str):
                judge_processor = SimpleProcessor(provider=judge_processor)
            else:
                judge_processor = SimpleProcessor(**judge_processor)

        # We call the judge directly with the synthesis prompt
        return judge_processor.process(
            file_path, 
            judge_prompt, 
            schema=schema, 
            model=model, 
            **kwargs
        )

    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        # Async version
        import asyncio
        
        # 1. Concurrent calls to all providers
        tasks = []
        for processor in self._providers:
            tasks.append(processor.aprocess(file_path, prompt, schema=schema, model=model, **kwargs))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.warning(f"Ensemble member {i+1} failed: {res}")
                continue
            
            processor = self._providers[i]
            all_results.append({
                "provider": processor._provider.__class__.__name__ if hasattr(processor, '_provider') else f"Model {i+1}",
                "result": res
            })

        if not all_results:
            raise RuntimeError("All ensemble members failed")
            
        if len(all_results) == 1:
            return all_results[0]["result"]
            
        # 2. Synthesize with judge
        results_str = json.dumps(all_results, indent=2)
        judge_prompt = self._synthesis_prompt.format(results=results_str)
        
        return await self._judge.aprocess(
            file_path, 
            judge_prompt, 
            schema=schema, 
            model=model, 
            **kwargs
        )
