"""
Fallback processor - retries extraction with backup providers.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .base import Processor
from ..providers.base import Provider

logger = logging.getLogger("strutex.processors.fallback")

class FallbackProcessor(Processor):
    """
    Processor that attempts extraction with a sequence of providers.
    
    Useful for cost optimization (try cheap model first) or reliability
    (fallback to powerful model if validation fails).
    
    Example:
        >>> processor = FallbackProcessor(
        ...     configs=[
        ...         {"provider": "gemini", "model_name": "gemini-1.5-flash"},
        ...         {"provider": "openai", "model_name": "gpt-4o"}
        ...     ]
        ... )
    """
    
    def __init__(
        self,
        configs: List[Dict[str, Any]],
        **kwargs
    ):
        """
        Args:
            configs: List of processor configurations to try in order.
                    Each dict should contain 'provider', and optionally 
                    'model_name', 'api_key', etc.
            **kwargs: Shared configuration for all fallbacks (security, cache, etc.)
        """
        # We don't call super().__init__ with a single provider here
        # as we manage a list of internal processors lazily.
        self._configs = configs
        self._shared_config = kwargs
        self._processors: List[Optional[Processor]] = [None] * len(configs)
        
    def _get_processor(self, index: int) -> Processor:
        """Lazily initialize the processor at the given index."""
        if self._processors[index] is None:
            config = {**self._shared_config, **self._configs[index]}
            # For simplicity, we use SimpleProcessor for each fallback step
            # but it could be any processor type if we added a 'type' key.
            from .simple import SimpleProcessor
            self._processors[index] = SimpleProcessor(**config)
        return self._processors[index] # type: ignore

    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        """
        Try providers in order until one succeeds and passes validation.
        """
        last_error = None
        
        for i in range(len(self._configs)):
            try:
                processor = self._get_processor(i)
                logger.info(f"Fallback step {i+1}/{len(self._configs)} using {processor._provider.__class__.__name__}")
                return processor.process(file_path, prompt, schema=schema, model=model, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback step {i+1} failed: {e}")
                last_error = e
                continue
                
        raise last_error or RuntimeError("All fallback steps failed")

    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        """Async version of process."""
        last_error = None
        
        for i in range(len(self._configs)):
            try:
                processor = self._get_processor(i)
                return await processor.aprocess(file_path, prompt, schema=schema, model=model, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback step {i+1} failed: {e}")
                last_error = e
                continue
                
        raise last_error or RuntimeError("All fallback steps failed")
