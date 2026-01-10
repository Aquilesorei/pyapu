"""
Verified Processor - N-times verification loop.

This processor performs extraction and then asks the LLM to verify and
correct its own output, improving accuracy at the cost of additional API calls.
"""

import json
import os
from typing import Any, Optional, Type, Union

from .base import Processor
from ..documents import get_mime_type
from ..plugins.base import SecurityPlugin
from ..types import Schema


class VerifiedProcessor(Processor):
    """
    Extraction processor with verification loop.
    
    Performs initial extraction, then asks the LLM to review and correct
    the result. This improves accuracy for complex documents at the cost
    of additional API calls.
    
    Example:
        ```python
        from strutex.processors import VerifiedProcessor
        from strutex import Object, String, Number
        
        processor = VerifiedProcessor(provider="gemini", verification_passes=2)
        schema = Object(properties={"total": Number(), "items": Array(...)})
        
        result = processor.process("invoice.pdf", "Extract all line items", schema)
        ```
    """
    
    DEFAULT_VERIFY_PROMPT = (
        "You are a strict data auditor. Your task is to verify the extracted data "
        "against the document provided.\n"
        "Review the data below. If it contains errors or missing fields that exist "
        "in the document, CORRECT them. If the data is correct, return it as is.\n"
        "Return the final validated JSON strictly adhering to the schema."
    )
    
    def __init__(
        self,
        *args,
        verification_passes: int = 1,
        verify_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize verified processor.
        
        Args:
            verification_passes: Number of verification passes.
            verify_prompt: Custom verification prompt.
            *args: Passed to Processor.__init__.
            **kwargs: Passed to Processor.__init__.
        """
        super().__init__(*args, **kwargs)
        self.verification_passes = verification_passes
        self.verify_prompt = verify_prompt or self.DEFAULT_VERIFY_PROMPT
    
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
        Process a document with verification.
        
        Args:
            file_path: Path to the document.
            prompt: Extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            security: Security configuration.
            **kwargs: Provider-specific options.
            
        Returns:
            Verified and potentially corrected result.
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
        
        result = self._provider.process(
            file_path=file_path,
            prompt=prompt,
            schema=schema,
            mime_type=mime_type,
            **kwargs
        )
        
        for _ in range(self.verification_passes):
            result = self._verify(file_path, result, schema, mime_type, **kwargs)
        
        if isinstance(result, dict):
            result = self._apply_security_output(result, effective_security)
            result = self._run_post_hooks(result, context)
            result = self._run_validation_chain(result, schema, file_path, mime_type)
        
        return self._validate_pydantic(result, pydantic_model)
    
    def _verify(
        self,
        file_path: str,
        result: Any,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """Perform one verification pass."""
        if hasattr(result, "model_dump_json"):
            result_str = result.model_dump_json()
        elif isinstance(result, dict):
            result_str = json.dumps(result, default=str)
        else:
            result_str = str(result)
        
        full_prompt = f"{self.verify_prompt}\n\n[EXTRACTED DATA TO VERIFY]:\n{result_str}"
        
        return self._provider.process(
            file_path=file_path,
            prompt=full_prompt,
            schema=schema,
            mime_type=mime_type,
            **kwargs
        )
    
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
        Async process a document with verification.
        
        Args:
            file_path: Path to the document.
            prompt: Extraction prompt.
            schema: Output schema.
            model: Pydantic model for output.
            security: Security configuration.
            **kwargs: Provider-specific options.
            
        Returns:
            Verified and potentially corrected result.
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
        
        result = await self._provider.aprocess(
            file_path=file_path,
            prompt=prompt,
            schema=schema,
            mime_type=mime_type,
            **kwargs
        )
        
        for _ in range(self.verification_passes):
            result = await self._averify(file_path, result, schema, mime_type, **kwargs)
        
        if isinstance(result, dict):
            result = self._apply_security_output(result, effective_security)
            result = self._run_post_hooks(result, context)
            
            import asyncio
            result = await asyncio.to_thread(
                self._run_validation_chain, result, schema, file_path, mime_type
            )
        
        return self._validate_pydantic(result, pydantic_model)
    
    async def _averify(
        self,
        file_path: str,
        result: Any,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """Async verification pass."""
        if hasattr(result, "model_dump_json"):
            result_str = result.model_dump_json()
        elif isinstance(result, dict):
            result_str = json.dumps(result, default=str)
        else:
            result_str = str(result)
        
        full_prompt = f"{self.verify_prompt}\n\n[EXTRACTED DATA TO VERIFY]:\n{result_str}"
        
        return await self._provider.aprocess(
            file_path=file_path,
            prompt=full_prompt,
            schema=schema,
            mime_type=mime_type,
            **kwargs
        )
