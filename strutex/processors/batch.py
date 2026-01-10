"""
Batch Processor - Parallel document processing.

This processor handles multiple documents concurrently using threads or asyncio.
"""

import asyncio
import concurrent.futures
from typing import Any, List, Optional, Type, Union

from .simple import SimpleProcessor
from ..context import BatchContext
from ..plugins.base import SecurityPlugin
from ..types import Schema


class BatchProcessor(SimpleProcessor):
    """
    Parallel document processing.
    
    Processes multiple documents concurrently using thread pool (sync)
    or asyncio.gather (async).
    
    Example:
        ```python
        from strutex.processors import BatchProcessor
        from strutex import Object, String
        
        processor = BatchProcessor(provider="gemini", max_workers=4)
        schema = Object(properties={"title": String()})
        
        files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
        batch_ctx = processor.process_batch(files, "Extract title", schema)
        
        for path, result in batch_ctx.results.items():
            print(f"{path}: {result}")
        ```
    """
    
    def __init__(self, *args, max_workers: int = 4, **kwargs):
        """
        Initialize batch processor.
        
        Args:
            max_workers: Maximum concurrent threads/tasks.
            *args: Passed to SimpleProcessor.__init__.
            **kwargs: Passed to SimpleProcessor.__init__.
        """
        super().__init__(*args, **kwargs)
        self.max_workers = max_workers
    
    def process_batch(
        self,
        file_paths: List[str],
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        security: Optional[Union[SecurityPlugin, bool]] = None,
        **kwargs
    ) -> BatchContext:
        """
        Process multiple documents in parallel using threads.
        
        Args:
            file_paths: List of document paths.
            prompt: Extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            security: Security configuration.
            **kwargs: Provider-specific options.
            
        Returns:
            BatchContext containing results and errors.
        """
        batch_ctx = BatchContext(total_documents=len(file_paths))
        
        def _process_one(path: str):
            try:
                result = self.process(path, prompt, schema, model, security, **kwargs)
                batch_ctx.add_result(path, result)
            except Exception as e:
                batch_ctx.add_error(path, e)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(executor.map(_process_one, file_paths))
        
        return batch_ctx
    
    async def aprocess_batch(
        self,
        file_paths: List[str],
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        security: Optional[Union[SecurityPlugin, bool]] = None,
        **kwargs
    ) -> BatchContext:
        """
        Process multiple documents in parallel using asyncio.
        
        Args:
            file_paths: List of document paths.
            prompt: Extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            security: Security configuration.
            **kwargs: Provider-specific options.
            
        Returns:
            BatchContext containing results and errors.
        """
        batch_ctx = BatchContext(total_documents=len(file_paths))
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def _aprocess_one(path: str):
            async with semaphore:
                try:
                    result = await self.aprocess(path, prompt, schema, model, security, **kwargs)
                    batch_ctx.add_result(path, result)
                except Exception as e:
                    batch_ctx.add_error(path, e)
        
        tasks = [_aprocess_one(path) for path in file_paths]
        await asyncio.gather(*tasks)
        
        return batch_ctx
