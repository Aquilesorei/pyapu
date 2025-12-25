"""
Document processor - main entry point for strutex extraction.

This module contains the core [`DocumentProcessor`][strutex.processor.DocumentProcessor]
class that orchestrates document extraction using pluggable LLM providers.
"""

import os
from typing import Any, Callable, Dict, List, Optional, Union, Type

from .documents import get_mime_type
from .types import Schema
from .plugins.registry import PluginRegistry
from .plugins.base import SecurityPlugin, SecurityResult
from .providers.base import Provider

# Type aliases for hook callbacks
PreProcessCallback = Callable[[str, str, Any, str, Dict[str, Any]], Optional[Dict[str, Any]]]
PostProcessCallback = Callable[[Dict[str, Any], Dict[str, Any]], Optional[Dict[str, Any]]]
ErrorCallback = Callable[[Exception, str, Dict[str, Any]], Optional[Dict[str, Any]]]


class _CallbackHookPlugin:
    """
    Wrapper that converts callback functions into a pluggy-compatible plugin.
    
    This allows callbacks registered via DocumentProcessor to integrate with
    the global pluggy hook system.
    """
    
    def __init__(
        self,
        pre_process_hooks: List[PreProcessCallback],
        post_process_hooks: List[PostProcessCallback],
        error_hooks: List[ErrorCallback],
    ):
        self._pre_process_hooks = pre_process_hooks
        self._post_process_hooks = post_process_hooks
        self._error_hooks = error_hooks
    
    def pre_process(
        self,
        file_path: str,
        prompt: str,
        schema: Any,
        mime_type: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute all pre-process callbacks."""
        result = None
        for hook in self._pre_process_hooks:
            try:
                hook_result = hook(file_path, prompt, schema, mime_type, context)
                if hook_result and isinstance(hook_result, dict):
                    result = hook_result
                    # Update prompt if modified
                    if "prompt" in hook_result:
                        prompt = hook_result["prompt"]
            except Exception:
                pass  # Hooks should not break processing
        return result
    
    def post_process(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute all post-process callbacks."""
        for hook in self._post_process_hooks:
            try:
                modified = hook(result, context)
                if modified is not None and isinstance(modified, dict):
                    result = modified
            except Exception:
                pass
        return result
    
    def on_error(
        self,
        error: Exception,
        file_path: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute error callbacks until one returns a fallback."""
        for hook in self._error_hooks:
            try:
                fallback = hook(error, file_path, context)
                if fallback is not None:
                    return fallback
            except Exception:
                pass
        return None


# Apply hookimpl markers to _CallbackHookPlugin methods
# This must be done at class definition time, not instance time
try:
    from .plugins.hooks import hookimpl, PLUGGY_AVAILABLE
    if PLUGGY_AVAILABLE:
        _CallbackHookPlugin.pre_process = hookimpl(_CallbackHookPlugin.pre_process)
        _CallbackHookPlugin.post_process = hookimpl(_CallbackHookPlugin.post_process)
        _CallbackHookPlugin.on_error = hookimpl(_CallbackHookPlugin.on_error)
except ImportError:
    pass


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

        With callbacks:

        ```python
        processor = DocumentProcessor(
            provider="gemini",
            on_post_process=lambda result, ctx: {**result, "processed": True}
        )
        ```

        With decorator:

        ```python
        processor = DocumentProcessor()

        @processor.on_post_process
        def add_timestamp(result, context):
            result["timestamp"] = datetime.now().isoformat()
            return result
        ```
    """

    def __init__(
        self,
        provider: Union[str, Provider] = "gemini",
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        security: Optional[SecurityPlugin] = None,
        on_pre_process: Optional[PreProcessCallback] = None,
        on_post_process: Optional[PostProcessCallback] = None,
        on_error: Optional[ErrorCallback] = None,
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
            on_pre_process: Callback called before processing. Receives
                (file_path, prompt, schema, mime_type, context) and can return
                a dict with modified values.
            on_post_process: Callback called after processing. Receives
                (result, context) and can return a modified result dict.
            on_error: Callback called on error. Receives (error, file_path, context)
                and can return a fallback result or None to propagate the error.

        Raises:
            ValueError: If the specified provider is not found in the registry.

        Example:
            ```python
            # Using callbacks
            processor = DocumentProcessor(
                provider="gemini",
                on_post_process=lambda result, ctx: normalize_dates(result)
            )
            ```
        """
        self.security = security

        # Hook storage: callbacks first, then decorated hooks
        self._pre_process_hooks: List[PreProcessCallback] = []
        self._post_process_hooks: List[PostProcessCallback] = []
        self._error_hooks: List[ErrorCallback] = []
        
        # Pluggy integration
        self._hook_plugin: Optional[_CallbackHookPlugin] = None
        self._hook_plugin_registered = False

        # Add initial callbacks if provided
        if on_pre_process:
            self._pre_process_hooks.append(on_pre_process)
        if on_post_process:
            self._post_process_hooks.append(on_post_process)
        if on_error:
            self._error_hooks.append(on_error)

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

    def _ensure_hooks_registered(self) -> None:
        """Register callback hooks with pluggy if not already done."""
        if self._hook_plugin_registered:
            return
            
        # Only register if we have any hooks
        if not (self._pre_process_hooks or self._post_process_hooks or self._error_hooks):
            return
            
        from .plugins.hooks import get_plugin_manager, PLUGGY_AVAILABLE
        
        if not PLUGGY_AVAILABLE:
            return
            
        pm = get_plugin_manager()
        if pm is None:
            return
            
        # Create and register the callback wrapper plugin
        self._hook_plugin = _CallbackHookPlugin(
            pre_process_hooks=self._pre_process_hooks,
            post_process_hooks=self._post_process_hooks,
            error_hooks=self._error_hooks,
        )
        pm.register(self._hook_plugin)
        self._hook_plugin_registered = True

    def __del__(self):
        """Unregister hooks when processor is garbage collected."""
        if self._hook_plugin_registered and self._hook_plugin:
            try:
                from .plugins.hooks import get_plugin_manager
                pm = get_plugin_manager()
                if pm:
                    pm.unregister(self._hook_plugin)
            except Exception:
                pass  # Ignore errors during cleanup

    # ==================== Decorator Methods ====================

    def on_pre_process(self, func: PreProcessCallback) -> PreProcessCallback:
        """
        Decorator to register a pre-process hook.

        The hook receives (file_path, prompt, schema, mime_type, context) and
        can return a dict with modified values for 'prompt' or other parameters.

        Example:
            ```python
            @processor.on_pre_process
            def add_instructions(file_path, prompt, schema, mime_type, context):
                return {"prompt": prompt + "\\nBe precise."}
            ```
        """
        self._pre_process_hooks.append(func)
        self._hook_plugin_registered = False  # Force re-registration
        return func

    def on_post_process(self, func: PostProcessCallback) -> PostProcessCallback:
        """
        Decorator to register a post-process hook.

        The hook receives (result, context) and can return a modified result dict.

        Example:
            ```python
            @processor.on_post_process
            def normalize_dates(result, context):
                result["date"] = parse_date(result.get("date"))
                return result
            ```
        """
        self._post_process_hooks.append(func)
        self._hook_plugin_registered = False  # Force re-registration
        return func

    def on_error(self, func: ErrorCallback) -> ErrorCallback:
        """
        Decorator to register an error hook.

        The hook receives (error, file_path, context) and can return a fallback
        result dict. Return None to propagate the original error.

        Example:
            ```python
            @processor.on_error
            def handle_rate_limit(error, file_path, context):
                if "rate limit" in str(error).lower():
                    return {"error": "Rate limited, please retry"}
                return None  # Propagate other errors
            ```
        """
        self._error_hooks.append(func)
        self._hook_plugin_registered = False  # Force re-registration
        return func

    # ==================== Main Processing ====================

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

        # Ensure hooks are registered with pluggy
        self._ensure_hooks_registered()

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

        # Create context for hooks
        context: Dict[str, Any] = {
            "file_path": file_path,
            "mime_type": mime_type,
            "kwargs": kwargs,
        }

        # Run pre-process hooks via pluggy
        from .plugins.hooks import call_hook
        pre_results = call_hook(
            "pre_process",
            file_path=file_path,
            prompt=prompt,
            schema=schema,
            mime_type=mime_type,
            context=context
        )
        # Apply any prompt modifications from hooks
        for hook_result in pre_results:
            if hook_result and isinstance(hook_result, dict) and "prompt" in hook_result:
                prompt = hook_result["prompt"]

        # Handle security
        effective_security = self._resolve_security(security)

        # Apply input security if enabled
        if effective_security:
            input_result = effective_security.validate_input(prompt)
            if not input_result.valid:
                raise SecurityError(f"Input rejected: {input_result.reason}")
            prompt = input_result.text or prompt

        # Process with provider (with error handling)
        try:
            result = self._provider.process(
                file_path=file_path,
                prompt=prompt,
                schema=schema,
                mime_type=mime_type,
                **kwargs
            )
        except Exception as e:
            # Run error hooks via pluggy
            error_results = call_hook(
                "on_error",
                error=e,
                file_path=file_path,
                context=context
            )
            # Use first non-None fallback
            fallback = None
            for hook_result in error_results:
                if hook_result is not None:
                    fallback = hook_result
                    break
            
            if fallback is not None:
                result = fallback
            else:
                raise  # Re-raise if no hook handled it

        # Apply output security if enabled
        if effective_security and isinstance(result, dict):
            output_result = effective_security.validate_output(result)
            if not output_result.valid:
                raise SecurityError(f"Output rejected: {output_result.reason}")
            result = output_result.data or result

        # Run post-process hooks via pluggy
        if isinstance(result, dict):
            post_results = call_hook(
                "post_process",
                result=result,
                context=context
            )
            # Apply modifications from hooks
            for hook_result in post_results:
                if hook_result is not None and isinstance(hook_result, dict):
                    result = hook_result

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