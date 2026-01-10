"""
Abstract Processor base class.

This module defines the abstract interface that all extraction processors must implement.
"""

import logging
import os
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union

from ..context import ProcessingContext
from ..documents import get_mime_type
from ..exceptions import SecurityError
from ..plugins.base import SecurityPlugin, Validator
from ..plugins.registry import PluginRegistry
from ..providers.base import Provider
from ..types import Schema
from ..validators.chain import ValidationChain

logger = logging.getLogger("strutex.processors")

PreProcessCallback = Callable[[str, str, Any, str, Dict[str, Any]], Optional[Dict[str, Any]]]
PostProcessCallback = Callable[[Dict[str, Any], Dict[str, Any]], Optional[Dict[str, Any]]]
ErrorCallback = Callable[[Exception, str, Dict[str, Any]], Optional[Dict[str, Any]]]


class Processor(ABC):
    """
    Abstract base class for all extraction processors.
    
    Provides shared infrastructure for provider resolution, caching, security,
    hooks, and validation. Subclasses implement specific extraction strategies.
    
    Attributes:
        provider: The LLM provider instance.
        cache: Optional cache backend for result caching.
        security: Optional security plugin for input/output validation.
        validation_chain: Chain of validators to run after extraction.
    """
    
    def __init__(
        self,
        provider: Union[str, Provider] = "gemini",
        model_name: str = "gemini-3-flash-preview",
        api_key: Optional[str] = None,
        cache: Optional[Any] = None,
        security: Optional[SecurityPlugin] = None,
        validators: Optional[List[Validator]] = None,
        on_pre_process: Optional[PreProcessCallback] = None,
        on_post_process: Optional[PostProcessCallback] = None,
        on_error: Optional[ErrorCallback] = None,
        **kwargs
    ):
        """
        Initialize the processor.
        
        Args:
            provider: Provider name or instance.
            model_name: LLM model name (when provider is a string).
            api_key: API key for the provider.
            cache: Optional cache backend.
            security: Optional security plugin.
            validators: Optional list of validators.
            on_pre_process: Pre-process callback.
            on_post_process: Post-process callback.
            on_error: Error callback.
            **kwargs: Additional configuration parameters.
        """
        # Store configuration for subclasses that need to instantiate internal processors
        self._config = {
            "provider": provider,
            "model_name": model_name,
            "api_key": api_key,
            "cache": cache,
            "security": security,
            "validators": validators,
            "on_pre_process": on_pre_process,
            "on_post_process": on_post_process,
            "on_error": on_error,
            **kwargs
        }
        
        self.cache = cache
        self.security = security
        self.validation_chain = ValidationChain(validators or [])
        
        self._pre_process_hooks: List[PreProcessCallback] = []
        self._post_process_hooks: List[PostProcessCallback] = []
        self._error_hooks: List[ErrorCallback] = []
        
        if on_pre_process:
            self._pre_process_hooks.append(on_pre_process)
        if on_post_process:
            self._post_process_hooks.append(on_post_process)
        if on_error:
            self._error_hooks.append(on_error)
        
        self._provider = self._resolve_provider(provider, model_name, api_key)
        self.provider_name = getattr(self._provider, 'name', type(self._provider).__name__)
    
    def _resolve_provider(
        self,
        provider: Union[str, Provider],
        model_name: str,
        api_key: Optional[str]
    ) -> Provider:
        """Resolve a provider string or instance to a Provider object."""
        if isinstance(provider, Provider):
            return provider
        
        provider_name = provider.lower()
        provider_cls = PluginRegistry.get("provider", provider_name)
        
        if provider_cls:
            return provider_cls(api_key=api_key, model=model_name)
        
        if provider_name in ("google", "gemini"):
            from ..providers.gemini import GeminiProvider
            return GeminiProvider(api_key=api_key, model=model_name)
        
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Available: {list(PluginRegistry.list('provider').keys())}"
        )
    
    def _resolve_security(
        self,
        override: Optional[Union[SecurityPlugin, bool]]
    ) -> Optional[SecurityPlugin]:
        """Resolve which security plugin to use."""
        if override is False:
            return None
        elif override is True:
            from ..security import default_security_chain
            return default_security_chain()
        elif override is not None:
            return override
        return self.security
    
    def _check_cache(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema]
    ) -> Optional[Any]:
        """Check if result is cached."""
        if self.cache is None:
            return None
        
        from ..cache import CacheKey
        cache_key = CacheKey.create(
            file_path=file_path,
            prompt=prompt,
            schema=schema,
            provider=self.provider_name,
            model=getattr(self._provider, 'model', None),
        )
        return self.cache.get(cache_key)
    
    def _store_cache(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema],
        result: Any
    ) -> None:
        """Store result in cache."""
        if self.cache is None:
            return
        
        from ..cache import CacheKey
        cache_key = CacheKey.create(
            file_path=file_path,
            prompt=prompt,
            schema=schema,
            provider=self.provider_name,
            model=getattr(self._provider, 'model', None),
        )
        self.cache.set(cache_key, result)
        logger.debug(f"Cached result for {file_path}")
    
    def _run_pre_hooks(
        self,
        file_path: str,
        prompt: str,
        schema: Any,
        mime_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Run pre-process hooks, returning potentially modified prompt."""
        from ..plugins.hooks import call_hook
        
        pre_results = call_hook(
            "pre_process",
            file_path=file_path,
            prompt=prompt,
            schema=schema,
            mime_type=mime_type,
            context=context
        )
        
        for hook_result in pre_results:
            if hook_result and isinstance(hook_result, dict) and "prompt" in hook_result:
                prompt = hook_result["prompt"]
        
        for hook in self._pre_process_hooks:
            try:
                result = hook(file_path, prompt, schema, mime_type, context)
                if result and isinstance(result, dict) and "prompt" in result:
                    prompt = result["prompt"]
            except Exception as e:
                logger.error(f"Error in pre-process hook: {e}")
        
        return prompt
    
    def _run_post_hooks(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run post-process hooks, returning potentially modified result."""
        from ..plugins.hooks import call_hook
        
        post_results = call_hook("post_process", result=result, context=context)
        for hook_result in post_results:
            if hook_result is not None and isinstance(hook_result, dict):
                result = hook_result
        
        for hook in self._post_process_hooks:
            try:
                modified = hook(result, context)
                if modified is not None and isinstance(modified, dict):
                    result = modified
            except Exception as e:
                logger.error(f"Error in post-process hook: {e}")
        
        return result
    
    def _run_error_hooks(
        self,
        error: Exception,
        file_path: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Run error hooks, returning fallback result if any."""
        from ..plugins.hooks import call_hook
        
        error_results = call_hook("on_error", error=error, file_path=file_path, context=context)
        for hook_result in error_results:
            if hook_result is not None:
                return hook_result
        
        for hook in self._error_hooks:
            try:
                fallback = hook(error, file_path, context)
                if fallback is not None:
                    return fallback
            except Exception as e:
                logger.error(f"Error in error hook: {e}")
        
        return None
    
    def _apply_security_input(
        self,
        prompt: str,
        security: Optional[SecurityPlugin]
    ) -> str:
        """Apply input security validation."""
        if security:
            input_result = security.validate_input(prompt)
            if not input_result.valid:
                raise SecurityError(f"Input rejected: {input_result.reason}")
            return input_result.text or prompt
        return prompt
    
    def _apply_security_output(
        self,
        result: Dict[str, Any],
        security: Optional[SecurityPlugin]
    ) -> Dict[str, Any]:
        """Apply output security validation."""
        if security and isinstance(result, dict):
            output_result = security.validate_output(result)
            if not output_result.valid:
                raise SecurityError(f"Output rejected: {output_result.reason}")
            return output_result.data or result
        return result
    
    def _run_validation_chain(
        self,
        result: Dict[str, Any],
        schema: Optional[Schema],
        file_path: str,
        mime_type: str
    ) -> Dict[str, Any]:
        """Run validation chain on result."""
        if not self.validation_chain.validators or not isinstance(result, dict):
            return result
        
        source_text = self._extract_source_text(file_path, mime_type)
        validation_result = self.validation_chain.validate(
            result,
            schema=schema,
            source_text=source_text
        )
        
        if not validation_result.valid:
            logger.warning(f"Validation failed: {validation_result.issues}")
        
        return validation_result.data
    
    def _extract_source_text(self, file_path: str, mime_type: str) -> Optional[str]:
        """Extract plain text from document for validation."""
        try:
            if mime_type == "application/pdf":
                from ..documents import pdf_to_text
                return pdf_to_text(file_path)
            elif mime_type in ("text/plain", "text/csv"):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            elif "spreadsheet" in mime_type or "excel" in mime_type:
                from ..documents import excel_to_csv_sheets
                sheets = excel_to_csv_sheets(file_path)
                return "\n\n".join(f"Sheet: {name}\n{content}" for name, content in sheets.items())
        except Exception as e:
            logger.warning(f"Failed to extract source text: {e}")
        return None
    
    def _convert_pydantic(
        self,
        model: Optional[Type]
    ) -> tuple[Optional[Schema], Optional[Type]]:
        """Convert Pydantic model to schema, returning (schema, original_model)."""
        if model is None:
            return None, None
        from ..pydantic_support import pydantic_to_schema
        return pydantic_to_schema(model), model
    
    def _validate_pydantic(self, result: Any, model: Optional[Type]) -> Any:
        """Validate result with Pydantic model if provided."""
        if model is not None:
            from ..pydantic_support import validate_with_pydantic
            return validate_with_pydantic(result, model)
        return result
    
    @abstractmethod
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        **kwargs
    ) -> Any:
        """
        Process a document and extract structured data.
        
        Args:
            file_path: Path to the document.
            prompt: Extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            **kwargs: Provider-specific options.
            
        Returns:
            Extracted data as dict or Pydantic model.
        """
        ...
    
    @abstractmethod
    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        **kwargs
    ) -> Any:
        """
        Async version of process.
        
        Args:
            file_path: Path to the document.
            prompt: Extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            **kwargs: Provider-specific options.
            
        Returns:
            Extracted data as dict or Pydantic model.
        """
        ...
    
    def _extract_from_text(
        self,
        text: str,
        prompt: str,
        schema: Optional[Schema] = None,
        schema_instructions: str = "",
        **kwargs
    ) -> Any:
        """
        Internal method used by RAG to perform structured extraction from raw text.
        
        This method leverages a temporary text file to reuse the standard
        provider processing pipeline, including hooks and security.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name
            
        try:
            # If we are called on a RagProcessor, we MUST use a simpler strategy
            # for the final extraction to avoid an infinite RAG recursion loop.
            # We can detect this by checking for 'rag' or using the provider directly.
            
            # Combine prompt with instructions if provided.
            full_prompt = prompt
            if schema_instructions:
                full_prompt = f"{prompt}\n\n{schema_instructions}"
                
            # Delegate to the provider's process method directly for the text chunk.
            # Note: We use the base process implementation via provider.
            mime_type = "text/plain"
            
            # Apply pre-hooks
            context = {"text_only": True, "kwargs": kwargs}
            full_prompt = self._run_pre_hooks(tmp_path, full_prompt, schema, mime_type, context)
            
            # Call provider
            result = self._provider.process(
                file_path=tmp_path,
                prompt=full_prompt,
                schema=schema,
                mime_type=mime_type,
                **kwargs
            )
            
            # Apply post-hooks and validation
            if isinstance(result, dict):
                result = self._run_post_hooks(result, context)
                result = self._run_validation_chain(result, schema, tmp_path, mime_type)
                
            return result
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def on_pre_process(self, func: PreProcessCallback) -> PreProcessCallback:
        """Decorator to register a pre-process hook."""
        self._pre_process_hooks.append(func)
        return func
    
    def on_post_process(self, func: PostProcessCallback) -> PostProcessCallback:
        """Decorator to register a post-process hook."""
        self._post_process_hooks.append(func)
        return func
    
    def on_error(self, func: ErrorCallback) -> ErrorCallback:
        """Decorator to register an error hook."""
        self._error_hooks.append(func)
        return func
