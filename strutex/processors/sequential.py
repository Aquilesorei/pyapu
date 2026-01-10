"""
Sequential processor - handles multi-page documents by processing segments sequentially.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .base import Processor
from .simple import SimpleProcessor

logger = logging.getLogger("strutex.processors.sequential")

class SequentialProcessor(Processor):
    """
    Processor for long documents that carries state across segments.
    
    Processes the document in chunks (e.g., page by page) and maintains
    a running context or summary to ensure consistency.
    """
    
    def __init__(
        self,
        processor: Optional[Processor] = None,
        chunk_size_pages: int = 1,
        overlap_pages: int = 0,
        **kwargs
    ):
        """
        Args:
            processor: The underlying processor to use for each segment.
            chunk_size_pages: Number of pages per segment.
            overlap_pages: Number of pages to overlap between segments.
            **kwargs: Shared configuration.
        """
        super().__init__(**kwargs)
        self._inner_processor = processor or SimpleProcessor(**self._config)
        self._chunk_size = chunk_size_pages
        self._overlap = overlap_pages
        
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        # Note: Real implementation would need a PDF extractor that supports page ranges.
        # For now, we provide the architectural skeleton.
        
        logger.info(f"Sequentially processing {file_path}")
        
        # 1. Initial extraction
        # In a real scenario, we'd split the file here.
        # For this skeleton, we'll assume a 'state' object that grows.
        
        current_state = {}
        
        # Mocking 3 segments
        for i in range(3):
            segment_prompt = (
                f"{prompt}\n\n"
                f"Current accumulated state: {current_state}\n"
                f"Continue extraction for segment {i+1}."
            )
            
            # Record the result
            result = self._inner_processor.process(
                file_path, 
                segment_prompt, 
                schema=schema, 
                model=model, 
                **kwargs
            )
            
            # Update state (very naive merge)
            if isinstance(result, dict):
                current_state.update(result)
            else:
                current_state = result # Fallback for non-dict results
                
        return current_state

    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Any] = None,
        model: Optional[Any] = None,
        **kwargs
    ) -> Any:
        # Async version is essentially the same but using await
        current_state = {}
        
        for i in range(3):
            segment_prompt = (
                f"{prompt}\n\n"
                f"Current accumulated state: {current_state}\n"
                f"Continue extraction for segment {i+1}."
            )
            
            result = await self._inner_processor.aprocess(
                file_path, 
                segment_prompt, 
                schema=schema, 
                model=model, 
                **kwargs
            )
            
            if isinstance(result, dict):
                current_state.update(result)
            else:
                current_state = result
                
        return current_state
