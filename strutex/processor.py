"""
Document processor - main entry point for strutex extraction.

This module contains the core [`DocumentProcessor`][strutex.processor.DocumentProcessor]
class that orchestrates document extraction using pluggable LLM providers.
"""

import os
from typing import Any, Optional, Union, Type

from .documents import get_mime_type
from .types import Schema
from .plugins.registry import PluginRegistry
from .plugins.base import SecurityPlugin, SecurityResult
from .providers.base import Provider


class DocumentProcessor:
    """
    Main document processing class for extracting structured data from documents.

    The `DocumentProcessor` orchestrates document extraction using pluggable providers,
    with optional security layer and Pydantic model support. It automatically detects
    file types, applies security checks, and validates output against schemas.

    Attributes:
        security: Optional security plugin/chain for input/output validation.

    Example:
        Basic usage with schema:

        ```python
        from strutex import DocumentProcessor, Object, String, Number

        schema = Object(properties={
            "invoice_number": String(),
            "total": Number()
        })

        processor = DocumentProcessor(provider="gemini")
        result = processor.process("invoice.pdf", "Extract data", schema)
        print(result["invoice_number"])
        ```

        With Pydantic model:

        ```python
        from pydantic import BaseModel

        class Invoice(BaseModel):
            invoice_number: str
            total: float

        result = processor.process("invoice.pdf", "Extract data", model=Invoice)
        # result is a validated Invoice instance
        ```

        With security enabled:

        ```python
        from strutex.security import default_security_chain

        processor = DocumentProcessor(
            provider="gemini",
            security=default_security_chain()
        )
        ```
    """

    def __init__(
        self,
        provider: Union[str, Provider] = "gemini",
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        security: Optional[SecurityPlugin] = None
    ):
        """
        Initialize the document processor.

        Args:
            provider: Provider name (e.g., "gemini", "openai") or a
                [`Provider`][strutex.plugins.base.Provider] instance.
            model_name: LLM model name to use (only when provider is a string).
            api_key: API key for the provider. Falls back to environment variables
                (e.g., `GOOGLE_API_KEY` for Gemini).
            security: Optional [`SecurityPlugin`][strutex.plugins.base.SecurityPlugin]
                or [`SecurityChain`][strutex.security.chain.SecurityChain] for
                input/output validation. Security is opt-in.

        Raises:
            ValueError: If the specified provider is not found in the registry.

        Example:
            ```python
            # Using provider name
            processor = DocumentProcessor(provider="gemini")

            # Using provider instance
            from strutex.providers import GeminiProvider
            processor = DocumentProcessor(provider=GeminiProvider(api_key="..."))
            ```
        """
        self.security = security

        # Resolve provider
        if isinstance(provider, str):
            provider_name = provider.lower()

            # Try to get from registry
            provider_cls = PluginRegistry.get("provider", provider_name)

            if provider_cls:
                self._provider = provider_cls(api_key=api_key, model=model_name)
            else:
                # Fallback for backward compatibility
                if provider_name in ("google", "gemini"):
                    from .providers.gemini import GeminiProvider
                    self._provider = GeminiProvider(api_key=api_key, model=model_name)
                else:
                    raise ValueError(f"Unknown provider: {provider}. Available: {list(PluginRegistry.list('provider').keys())}")
        else:
            # Provider instance passed directly
            self._provider = provider

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
        Process a document and extract structured data.

        This method automatically detects the file type, applies security validation
        (if enabled), sends the document to the LLM provider, and validates the output.

        Args:
            file_path: Absolute path to the source file (PDF, Excel, or Image).
            prompt: Natural language instruction for extraction.
            schema: A [`Schema`][strutex.types.Schema] definition. Mutually exclusive
                with `model`.
            model: A Pydantic `BaseModel` class. Mutually exclusive with `schema`.
                If provided, returns a validated Pydantic instance.
            security: Override security setting for this request.
                - `True`: Use default security chain
                - `False`: Disable security
                - `SecurityPlugin`: Use specific plugin
                - `None`: Use processor default
            **kwargs: Additional provider-specific options.

        Returns:
            Extracted data as a dictionary, or a Pydantic model instance if `model`
            was provided.

        Raises:
            FileNotFoundError: If `file_path` does not exist.
            ValueError: If neither `schema` nor `model` is provided.
            SecurityError: If security validation fails (input or output rejected).

        Example:
            ```python
            result = processor.process(
                file_path="invoice.pdf",
                prompt="Extract invoice number and total amount",
                schema=invoice_schema
            )
            print(result["total"])
            ```
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Handle Pydantic model
        pydantic_model = None
        if model is not None:
            from .pydantic_support import pydantic_to_schema
            schema = pydantic_to_schema(model)
            pydantic_model = model

        if schema is None:
            raise ValueError("Either 'schema' or 'model' must be provided")

        # Detect MIME type
        mime_type = get_mime_type(file_path)

        # Handle security
        effective_security = self._resolve_security(security)

        # Apply input security if enabled
        if effective_security:
            input_result = effective_security.validate_input(prompt)
            if not input_result.valid:
                raise SecurityError(f"Input rejected: {input_result.reason}")
            prompt = input_result.text or prompt

        # Process with provider
        result = self._provider.process(
            file_path=file_path,
            prompt=prompt,
            schema=schema,
            mime_type=mime_type,
            **kwargs
        )

        # Apply output security if enabled
        if effective_security and isinstance(result, dict):
            output_result = effective_security.validate_output(result)
            if not output_result.valid:
                raise SecurityError(f"Output rejected: {output_result.reason}")
            result = output_result.data or result

        # Validate with Pydantic if model was provided
        if pydantic_model is not None:
            from .pydantic_support import validate_with_pydantic
            result = validate_with_pydantic(result, pydantic_model)

        return result

    def _resolve_security(
        self,
        override: Optional[Union[SecurityPlugin, bool]]
    ) -> Optional[SecurityPlugin]:
        """Resolve which security plugin to use."""
        if override is False:
            return None
        elif override is True:
            from .security import default_security_chain
            return default_security_chain()
        elif override is not None:
            return override
        else:
            return self.security  # Use instance default


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