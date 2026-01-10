"""
Simple Processor - Single LLM call extraction.

This is the most basic extraction strategy: send the document to the LLM once
and return the structured result.
"""

import os
from typing import Any, Optional, Type, Union

from .base import Processor
from ..documents import get_mime_type
from ..plugins.base import SecurityPlugin
from ..types import Schema


class SimpleProcessor(Processor):
    """
    Single-call extraction processor.
    
    Sends the document to the LLM provider once and returns the structured result.
    This is the fastest and most cost-effective strategy for high-quality documents.
    
    Example:
        ```python
        from strutex.processors import SimpleProcessor
        from strutex import Object, String
        
        processor = SimpleProcessor(provider="gemini")
        schema = Object(properties={"title": String(), "author": String()})
        
        result = processor.process("document.pdf", "Extract metadata", schema)
        ```
    """
    
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        security: Optional[Union[SecurityPlugin, bool]] = None,
        **kwargs
    ) -> Any:
        """
        Process a document with a single LLM call.
        
        Args:
            file_path: Path to the document.
            prompt: Extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            security: Security configuration.
            **kwargs: Provider-specific options.
            
        Returns:
            Extracted data as dict or Pydantic model.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        pydantic_schema, pydantic_model = self._convert_pydantic(model)
        if pydantic_schema:
            schema = pydantic_schema
        
        if schema is None:
            raise ValueError("Either 'schema' or 'model' must be provided")
        
        mime_type = get_mime_type(file_path)
        context = {"file_path": file_path, "mime_type": mime_type, "kwargs": kwargs}
        
        prompt = self._run_pre_hooks(file_path, prompt, schema, mime_type, context)
        
        effective_security = self._resolve_security(security)
        prompt = self._apply_security_input(prompt, effective_security)
        
        cached = self._check_cache(file_path, prompt, schema)
        if cached is not None:
            if isinstance(cached, dict):
                cached = self._run_post_hooks(cached, context)
            return self._validate_pydantic(cached, pydantic_model)
        
        try:
            result = self._provider.process(
                file_path=file_path,
                prompt=prompt,
                schema=schema,
                mime_type=mime_type,
                **kwargs
            )
            
            self._store_cache(file_path, prompt, schema, result)
            
        except Exception as e:
            fallback = self._run_error_hooks(e, file_path, context)
            if fallback is not None:
                result = fallback
            else:
                raise
        
        if isinstance(result, dict):
            result = self._apply_security_output(result, effective_security)
            result = self._run_post_hooks(result, context)
            result = self._run_validation_chain(result, schema, file_path, mime_type)
        
        return self._validate_pydantic(result, pydantic_model)
    
    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        security: Optional[Union[SecurityPlugin, bool]] = None,
        **kwargs
    ) -> Any:
        """
        Async process a document with a single LLM call.
        
        Args:
            file_path: Path to the document.
            prompt: Extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            security: Security configuration.
            **kwargs: Provider-specific options.
            
        Returns:
            Extracted data as dict or Pydantic model.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        pydantic_schema, pydantic_model = self._convert_pydantic(model)
        if pydantic_schema:
            schema = pydantic_schema
        
        if schema is None:
            raise ValueError("Either 'schema' or 'model' must be provided")
        
        mime_type = get_mime_type(file_path)
        context = {"file_path": file_path, "mime_type": mime_type, "kwargs": kwargs}
        
        prompt = self._run_pre_hooks(file_path, prompt, schema, mime_type, context)
        
        effective_security = self._resolve_security(security)
        prompt = self._apply_security_input(prompt, effective_security)
        
        cached = self._check_cache(file_path, prompt, schema)
        if cached is not None:
            if isinstance(cached, dict):
                cached = self._run_post_hooks(cached, context)
            return self._validate_pydantic(cached, pydantic_model)
        
        try:
            result = await self._provider.aprocess(
                file_path=file_path,
                prompt=prompt,
                schema=schema,
                mime_type=mime_type,
                **kwargs
            )
            
            self._store_cache(file_path, prompt, schema, result)
            
        except Exception as e:
            fallback = self._run_error_hooks(e, file_path, context)
            if fallback is not None:
                result = fallback
            else:
                raise
        
        if isinstance(result, dict):
            result = self._apply_security_output(result, effective_security)
            result = self._run_post_hooks(result, context)
            
            import asyncio
            result = await asyncio.to_thread(
                self._run_validation_chain, result, schema, file_path, mime_type
            )
        
        return self._validate_pydantic(result, pydantic_model)
