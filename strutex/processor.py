"""
Document processor - main entry point for strutex extraction.

This module contains the core [`DocumentProcessor`][strutex.processor.DocumentProcessor]
class that orchestrates document extraction using pluggable LLM providers.
"""

import json
import logging
import os
from enum import StrEnum
from typing import Any, Callable, Dict, List, Optional, Union, Type

logger = logging.getLogger("strutex.processor")

from .documents import get_mime_type
from .types import Schema
from .context import BatchContext
from .exceptions import SecurityError
from .providers.base import Provider
from .plugins.base import SecurityPlugin, Validator

# Type aliases for hook callbacks
PreProcessCallback = Callable[[str, str, Any, str, Dict[str, Any]], Optional[Dict[str, Any]]]
PostProcessCallback = Callable[[Dict[str, Any], Dict[str, Any]], Optional[Dict[str, Any]]]
ErrorCallback = Callable[[Exception, str, Dict[str, Any]], Optional[Dict[str, Any]]]


class ExtractionStrategy(StrEnum):
    ONCE = "ONCE"
    ENSEMBLE="ENSEMBLE" # semantic search
    VOTE = "VOTE"
    RAG = "RAG"


from .processors import (
    Processor,
    SimpleProcessor, 
    VerifiedProcessor, 
    RagProcessor, 
    BatchProcessor,
    FallbackProcessor,
    RouterProcessor,
    EnsembleProcessor,
    SequentialProcessor,
    PrivacyProcessor,
    ActiveLearningProcessor,
    AgenticProcessor
)


class DocumentProcessor:
    """
    Facade for document processing, providing backwards compatibility.

    This class delegates to specialized processor implementations:
    - SimpleProcessor: For single-call extraction.
    - VerifiedProcessor: For extraction with verification.
    - RagProcessor: For retrieval-augmented generation.
    - BatchProcessor: For parallel processing.
    """

    def __init__(
        self,
        provider: Union[str, Provider] = "gemini",
        model_name: str = "gemini-3-flash-preview",
        api_key: Optional[str] = None,
        security: Optional[SecurityPlugin] = None,
        cache: Optional[Any] = None,
        on_pre_process: Optional[PreProcessCallback] = None,
        on_post_process: Optional[PostProcessCallback] = None,
        on_error: Optional[ErrorCallback] = None,
        validators: Optional[List[Validator]] = None,
    ):
        """Initialize the document processor facade."""
        # Generic config for all internal processors
        self._config = {
            "provider": provider,
            "model_name": model_name,
            "api_key": api_key,
            "security": security,
            "cache": cache,
            "validators": validators,
            "on_pre_process": on_pre_process,
            "on_post_process": on_post_process,
            "on_error": on_error,
        }
        
        # Lazy-loaded processors
        self._simple: Optional[SimpleProcessor] = None
        self._verified: Optional[VerifiedProcessor] = None
        self._rag: Optional[RagProcessor] = None
        self._batch: Optional[BatchProcessor] = None
        self._fallback: Optional[FallbackProcessor] = None
        self._router: Optional[RouterProcessor] = None
        self._ensemble: Optional[EnsembleProcessor] = None
        self._sequential: Optional[SequentialProcessor] = None
        self._privacy: Optional[PrivacyProcessor] = None
        self._active: Optional[ActiveLearningProcessor] = None
        self._agentic: Optional[AgenticProcessor] = None

    @property
    def simple(self) -> SimpleProcessor:
        """Get the simple processor instance."""
        if self._simple is None:
            self._simple = SimpleProcessor(**self._config)
        return self._simple

    @property
    def verified(self) -> VerifiedProcessor:
        """Get the verified processor instance."""
        if self._verified is None:
            self._verified = VerifiedProcessor(**self._config)
        return self._verified

    @property
    def rag(self) -> RagProcessor:
        """Get the RAG processor instance."""
        if self._rag is None:
            self._rag = RagProcessor(**self._config)
        return self._rag

    @property
    def batch(self) -> BatchProcessor:
        """Get the batch processor instance."""
        if self._batch is None:
            self._batch = BatchProcessor(**self._config)
        return self._batch

    def create_fallback(self, configs: List[Dict[str, Any]]) -> FallbackProcessor:
        """Create a custom fallback processor."""
        return FallbackProcessor(configs=configs, **self._config)

    def create_router(self, routes: Dict[str, Processor], **kwargs) -> RouterProcessor:
        """Create a custom router processor."""
        return RouterProcessor(routes=routes, **self._config, **kwargs)

    def create_ensemble(self, providers: List[Processor], **kwargs) -> EnsembleProcessor:
        """Create a custom ensemble processor."""
        return EnsembleProcessor(providers=providers, **self._config, **kwargs)

    def create_sequential(self, **kwargs) -> SequentialProcessor:
        """Create a custom sequential processor."""
        return SequentialProcessor(**self._config, **kwargs)

    def create_privacy(self, **kwargs) -> PrivacyProcessor:
        """Create a custom privacy processor."""
        return PrivacyProcessor(**self._config, **kwargs)

    @property
    def agentic(self) -> AgenticProcessor:
        """Get the agentic processor instance."""
        if self._agentic is None:
            self._agentic = AgenticProcessor(**self._config)
        return self._agentic

    def create_active(self, **kwargs) -> ActiveLearningProcessor:
        """Create a custom active learning processor."""
        return ActiveLearningProcessor(**self._config, **kwargs)

    @property
    def _provider(self) -> Provider:
        """Backwards compatibility for tests and internal access."""
        return self.simple._provider

    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        security: Optional[Union[SecurityPlugin, bool]] = None,
        verify: bool = False,
        **kwargs
    ) -> Any:
        """Process a document (delegates to Simple or Verified processor)."""
        if verify:
            return self.verified.process(file_path, prompt, schema, model, security=security, **kwargs)
        return self.simple.process(file_path, prompt, schema, model, security=security, **kwargs)

    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        security: Optional[Union[SecurityPlugin, bool]] = None,
        verify: bool = False,
        **kwargs
    ) -> Any:
        """Async process a document."""
        if verify:
            return await self.verified.aprocess(file_path, prompt, schema, model, security=security, **kwargs)
        return await self.simple.aprocess(file_path, prompt, schema, model, security=security, **kwargs)

    def verify(
        self,
        file_path: str,
        result: Any,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        verify_prompt: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Verify an existing result."""
        # Create a temporary verified processor with specific prompt if needed
        proc = self.verified
        if verify_prompt:
            proc = VerifiedProcessor(**{**self._config, "verify_prompt": verify_prompt})
        return proc._verify(file_path, result, schema or proc._convert_pydantic(model)[0], get_mime_type(file_path), **kwargs)

    def rag_ingest(self, file_path: str, collection_name: Optional[str] = None):
        """Ingest document for RAG."""
        return self.rag.ingest(file_path, collection=collection_name)

    def rag_query(
        self, 
        query: str, 
        collection_name: Optional[str] = None,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None
    ) -> Any:
        """Perform RAG query."""
        return self.rag.query(query, collection=collection_name, schema=schema, model=model)

    def process_batch(
        self,
        file_paths: List[str],
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        max_workers: int = 4,
        **kwargs
    ) -> BatchContext:
        """Process documents in batch."""
        # Update batch processor workers if different
        self.batch.max_workers = max_workers
        return self.batch.process_batch(file_paths, prompt, schema, model, **kwargs)

    async def aprocess_batch(
        self,
        file_paths: List[str],
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        max_concurrency: int = 4,
        **kwargs
    ) -> BatchContext:
        """Async process documents in batch."""
        self.batch.max_workers = max_concurrency
        return await self.batch.aprocess_batch(file_paths, prompt, schema, model, **kwargs)

    # Decorators map to simple processor hooks (shared config would be better but this works for compatibility)
    def on_pre_process(self, func: PreProcessCallback) -> PreProcessCallback:
        """Register pre-process hook."""
        self._config["on_pre_process"] = func
        # If processors already exist, update them
        if self._simple: self._simple.on_pre_process(func)
        if self._verified: self._verified.on_pre_process(func)
        if self._rag: self._rag.on_pre_process(func)
        if self._batch: self._batch.on_pre_process(func)
        return func

    def on_post_process(self, func: PostProcessCallback) -> PostProcessCallback:
        """Register post-process hook."""
        self._config["on_post_process"] = func
        if self._simple: self._simple.on_post_process(func)
        if self._verified: self._verified.on_post_process(func)
        if self._rag: self._rag.on_post_process(func)
        if self._batch: self._batch.on_post_process(func)
        return func

    def on_error(self, func: ErrorCallback) -> ErrorCallback:
        """Register error hook."""
        self._config["on_error"] = func
        if self._simple: self._simple.on_error(func)
        if self._verified: self._verified.on_error(func)
        if self._rag: self._rag.on_error(func)
        if self._batch: self._batch.on_error(func)
        return func


class SecurityError(Exception):
    """
    Raised when security validation fails.

    This exception is raised when either input validation (e.g., prompt injection
    detected) or output validation (e.g., leaked secrets detected) fails.

    Attributes:
        message: Description of the security failure.

    Example:
        ```python
        from strutex.processor import SecurityError

        try:
            result = processor.process(file, prompt, schema, security=True)
        except SecurityError as e:
            print(f"Security check failed: {e}")
        ```
    """
    pass