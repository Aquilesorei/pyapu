"""
Plugin system for strutex extensibility.

Provides the PluginRegistry for registering and discovering plugins,
the @register decorator for easy plugin registration, and base classes
for all plugin types.

Plugin System v2 Features:
- Lazy loading: Plugins are only imported when first used
- Entry points: Auto-discover plugins from installed packages
- Hooks: Pluggy-based hooks for pipeline extension
- Protocols: Type-safe interfaces for mypy compatibility
- Sandboxing: Safe probing of untrusted plugins

Example:
    # Get a provider (lazy loaded)
    >>> from strutex.plugins import PluginRegistry
    >>> provider_cls = PluginRegistry.get("provider", "gemini")
    
    # Register your own plugin
    >>> from strutex.plugins import register, Provider
    >>> 
    >>> @register("provider")
    >>> class MyProvider(Provider):
    ...     def process(self, ...): ...
"""

from .registry import (
    PluginRegistry,
    register,
    provider,
    extractor,
    validator,
    postprocessor,
    security,
)
from .base import (
    Provider,
    Extractor,
    Validator,
    ValidationResult,
    Postprocessor,
    SecurityPlugin,
    SecurityResult
)
from .protocol import (
    PLUGIN_API_VERSION,
    PLUGIN_PROTOCOLS,
    ProviderProtocol,
    ExtractorProtocol,
    ValidatorProtocol,
    PostprocessorProtocol,
    SecurityPluginProtocol,
    check_plugin_version,
    validate_plugin_protocol,
)
from .hooks import (
    hookspec,
    hookimpl,
    StrutexHookSpec,
    get_plugin_manager,
    register_hook_plugin,
    call_hook,
)

from  .plugin_type import  PluginType

__all__ = [
    # Registry
    "PluginRegistry",
    "register",
    
    # Convenience decorators
    "provider",
    "extractor",
    "validator",
    "postprocessor",
    "security",
    
    # Base classes
    "Provider",
    "Extractor",
    "Validator",
    "ValidationResult",
    "Postprocessor",
    "SecurityPlugin",
    "SecurityResult",
    
    # Protocols
    "PLUGIN_API_VERSION",
    "PluginType",
    "PLUGIN_PROTOCOLS",
    "ProviderProtocol",
    "ExtractorProtocol",
    "ValidatorProtocol",
    "PostprocessorProtocol",
    "SecurityPluginProtocol",
    "check_plugin_version",
    "validate_plugin_protocol",
    
    # Hooks
    "hookspec",
    "hookimpl",
    "StrutexHookSpec",
    "get_plugin_manager",
    "register_hook_plugin",
    "call_hook",
]
