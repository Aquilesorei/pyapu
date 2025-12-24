"""
Pluggy hook specifications

Provides hook specifications that define extension points in the strutex
processing pipeline. Plugins can implement these hooks to extend or
modify behavior at various stages.

Example:
    >>> from strutex.plugins.hooks import hookimpl
    >>> 
    >>> class MyPlugin:
    >>>     @hookimpl
    >>>     def strutex_post_process(self, result: dict) -> dict:
    >>>         return normalize_dates(result)
"""

from typing import Any, Dict, List, Optional

try:
    import pluggy
    PLUGGY_AVAILABLE = True
except ImportError:
    PLUGGY_AVAILABLE = False
    # Provide stub decorators when pluggy is not installed
    class _StubMarker:
        def __init__(self, project_name: str = ""):
            self.project_name = project_name
        
        def __call__(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    class _StubPluggy:
        HookspecMarker = _StubMarker
        HookimplMarker = _StubMarker
        PluginManager = None
    
    pluggy = _StubPluggy()

# Hook markers for strutex
hookspec = pluggy.HookspecMarker("strutex")
hookimpl = pluggy.HookimplMarker("strutex")


class StrutexHookSpec:
    """
    Hook specifications for the  plugin system.
    
    These define the extension points where plugins can inject
    custom behavior into the processing pipeline.
    """
    
    @hookspec
    def register_providers(self) -> List[type]:
        """
        Return a list of provider classes to register.
        
        Called during plugin discovery to allow dynamic registration
        of providers without entry points.
        
        Returns:
            List of Provider subclasses
        
        Example:
            @hookimpl
            def strutex_register_providers(self):
                return [MyProvider, AnotherProvider]
        """
        pass
    
    @hookspec
    def register_validators(self) -> List[type]:
        """
        Return a list of validator classes to register.
        
        Returns:
            List of Validator subclasses
        """
        pass
    
    @hookspec
    def register_postprocessors(self) -> List[type]:
        """
        Return a list of postprocessor classes to register.
        
        Returns:
            List of Postprocessor subclasses
        """
        pass
    
    @hookspec
    def register_security(self) -> List[type]:
        """
        Return a list of security plugin classes to register.
        
        Returns:
            List of SecurityPlugin subclasses
        """
        pass
    
    @hookspec
    def register_extractors(self) -> List[type]:
        """
        Return a list of extractor classes to register.
        
        Returns:
            List of Extractor subclasses
        """
        pass
    
    @hookspec(firstresult=False)
    def pre_process(
        self,
        file_path: str,
        prompt: str,
        schema: Any,
        mime_type: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Hook called before document processing.
        
        Can modify inputs or perform pre-processing tasks.
        All registered hooks are called in priority order.
        
        Args:
            file_path: Path to the document
            prompt: Extraction prompt
            schema: Expected output schema
            mime_type: MIME type of the document
            context: Mutable context dict for sharing state
            
        Returns:
            Optional dict with modified values, or None to keep original
        
        Example:
            @hookimpl
            def strutex_pre_process(self, file_path, prompt, schema, mime_type, context):
                context["start_time"] = time.time()
                return {"prompt": prompt + "\\nAdditional instruction."}
        """
        pass
    
    @hookspec(firstresult=False)
    def post_process(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Hook called after document processing.
        
        Can transform or validate the extraction result.
        All registered hooks are called in priority order.
        
        Args:
            result: The extracted data
            context: Context dict from pre_process
            
        Returns:
            Optional dict with modified result, or None to keep original
        
        Example:
            @hookimpl
            def strutex_post_process(self, result, context):
                elapsed = time.time() - context.get("start_time", 0)
                result["_processing_time"] = elapsed
                return result
        """
        pass
    
    @hookspec(firstresult=True)
    def on_error(
        self,
        error: Exception,
        file_path: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Hook called when an error occurs during processing.
        
        First plugin to return a result wins (error recovery).
        
        Args:
            error: The exception that occurred
            file_path: Path to the document being processed
            context: Context dict
            
        Returns:
            Optional fallback result, or None to propagate error
        
        Example:
            @hookimpl
            def strutex_on_error(self, error, file_path, context):
                if isinstance(error, RateLimitError):
                    return self._cached_result(file_path)
                return None
        """
        pass


# Global plugin manager instance
_plugin_manager: Optional["pluggy.PluginManager"] = None


def get_plugin_manager() -> Optional["pluggy.PluginManager"]:
    """
    Get or create the global plugin manager.
    
    Returns:
        PluginManager instance, or None if pluggy is not installed
    """
    global _plugin_manager
    
    if not PLUGGY_AVAILABLE:
        return None
    
    if _plugin_manager is None:
        _plugin_manager = pluggy.PluginManager("strutex")
        _plugin_manager.add_hookspecs(StrutexHookSpec)
    
    return _plugin_manager


def register_hook_plugin(plugin: Any) -> None:
    """
    Register a plugin with hook implementations.
    
    Args:
        plugin: An object with @hookimpl decorated methods
        
    Raises:
        RuntimeError: If pluggy is not installed
    """
    pm = get_plugin_manager()
    if pm is None:
        raise RuntimeError("pluggy is required for hook plugins. Install with: pip install pluggy")
    
    pm.register(plugin)


def unregister_hook_plugin(plugin: Any) -> None:
    """
    Unregister a previously registered hook plugin.
    
    Args:
        plugin: The plugin object to unregister
    """
    pm = get_plugin_manager()
    if pm is not None:
        pm.unregister(plugin)


def call_hook(hook_name: str, **kwargs) -> List[Any]:
    """
    Call a hook by name with the given arguments.
    
    Args:
        hook_name: Name of the hook to call
        **kwargs: Arguments to pass to hook implementations
        
    Returns:
        List of results from all hook implementations
    """
    pm = get_plugin_manager()
    if pm is None:
        return []
    
    hook = getattr(pm.hook, hook_name, None)
    if hook is None:
        return []
    
    return hook(**kwargs)
