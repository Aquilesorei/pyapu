"""
Active learning processor - calculates confidence and flags for review.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .base import Processor
from .simple import SimpleProcessor

logger = logging.getLogger("strutex.processors.active")

class ActiveLearningProcessor(Processor):
    """
    Processor that assesses extraction confidence.
    
    Adds metadata fields to the result:
    - `_confidence`: Estimated accuracy (0.0 to 1.0)
    - `_requires_review`: Boolean flag for human intervention
    """
    
    def __init__(
        self,
        processor: Optional[Processor] = None,
        confidence_threshold: float = 0.85,
        num_trials: int = 1,
        **kwargs
    ):
        """
        Args:
            processor: Underlyng processor to use.
            confidence_threshold: Scores below this flag for review.
            num_trials: Number of times to run extraction to check for consistency.
            **kwargs: Shared configuration.
        """
        super().__init__(**kwargs)
        self._inner_processor = processor or SimpleProcessor(**self._config)
        self._threshold = confidence_threshold
        self._num_trials = num_trials
        
    def _calculate_confidence(self, results: List[Any]) -> float:
        """Estimate confidence based on consistency or model signals."""
        if len(results) == 1:
            # Fallback score if only 1 trial
            return 0.9 
            
        # If multiple trials, we can check how many match the majority
        # Very simple version:
        matches = 0
        first = results[0]
        for r in results:
            if r == first:
                matches += 1
        return matches / len(results)

    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        results = []
        for _ in range(self._num_trials):
            res = self._inner_processor.process(file_path, prompt, schema=schema, model=model, **kwargs)
            results.append(res)
            
        confidence = self._calculate_confidence(results)
        
        final_result = results[0]
        if isinstance(final_result, dict):
            final_result["_confidence"] = confidence
            final_result["_requires_review"] = confidence < self._threshold
            
        logger.info(f"Extraction confidence: {confidence:.2f} (Review: {final_result.get('_requires_review')})")
        return final_result

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
        tasks = [
            self._inner_processor.aprocess(file_path, prompt, schema=schema, model=model, **kwargs)
            for _ in range(self._num_trials)
        ]
        results = await asyncio.gather(*tasks)
        
        confidence = self._calculate_confidence(results)
        final_result = results[0]
        if isinstance(final_result, dict):
            final_result["_confidence"] = confidence
            final_result["_requires_review"] = confidence < self._threshold
            
        return final_result
