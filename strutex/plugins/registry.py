"""
Plugin registry with lazy loading and entry point discovery.

This module provides the central registry for all strutex plugins. It supports:
- Lazy loading: Plugins are only imported when first used
- Entry points: Auto-discover plugins from installed packages
- Decorator registration: Backwards-compatible @register decorator
- Version checking: Validate plugin API compatibility

Example:
    # Get a provider (lazy loaded from entry point)
    >>> provider_cls = PluginRegistry.get("provider", "gemini")
    >>> provider = provider_cls()
    
    # List all discovered plugins
    >>> PluginRegistry.list("provider")
    {'gemini': <class 'strutex.providers.gemini.GeminiProvider'>}
"""

import sys
import warnings
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from abc import ABC

from .protocol import PLUGIN_API_VERSION, check_plugin_version


# Type for entry point objects
if sys.version_info >= (3, 10):
    from importlib.metadata import EntryPoint
else:
    try:
        from importlib_metadata import EntryPoint
    except ImportError:
        EntryPoint = Any  # Fallback type


class PluginRegistry:
    """
    Central registry for all plugin types with lazy loading.
    
    Plugins are stored as EntryPoint objects and only loaded when
    first accessed via get(). This improves startup time and avoids
    importing unused dependencies.
    
    Usage:
        # Get a plugin (loads on first access)
        cls = PluginRegistry.get("provider", "gemini")
        
        # List all plugins (does not load them)
        all_providers = PluginRegistry.list("provider")
        
        # Force discovery from entry points
        count = PluginRegistry.discover()
    """
    
    # Store EntryPoint objects (not loaded yet)
    _entry_points: Dict[str, Dict[str, "EntryPoint"]] = {}
    
    # Cache of loaded plugin classes
    _loaded: Dict[str, Dict[str, Type]] = {}
    
    # Manually registered plugins (from @register decorator)
    _manual: Dict[str, Dict[str, Type]] = {}
    
    # Track if discovery has been run
    _discovered: bool = False
    
    @classmethod
    def register(cls, plugin_type: str, name: str, plugin_cls: Type) -> None:
        """
        Register a plugin class manually.
        
        This is used by the @register decorator for backwards compatibility.
        Prefer using entry points in pyproject.toml for new plugins.
        
        Args:
            plugin_type: Type of plugin (e.g., "provider", "security", "validator")
            name: Unique name for this plugin
            plugin_cls: The plugin class to register
        """
        if plugin_type not in cls._manual:
            cls._manual[plugin_type] = {}
        
        cls._manual[plugin_type][name.lower()] = plugin_cls
        
        # Also add to loaded cache
        if plugin_type not in cls._loaded:
            cls._loaded[plugin_type] = {}
        cls._loaded[plugin_type][name.lower()] = plugin_cls
    
    @classmethod
    def get(cls, plugin_type: str, name: str) -> Optional[Type]:
        """
        Get a registered plugin class by type and name.
        
        If the plugin is registered via entry point and not yet loaded,
        it will be loaded on first access (lazy loading).
        
        Args:
            plugin_type: Type of plugin
            name: Name of the plugin
            
        Returns:
            The plugin class, or None if not found
        """
        name_lower = name.lower()
        
        # Ensure discovery has run
        if not cls._discovered:
            cls.discover()
        
        # Check loaded cache first
        if name_lower in cls._loaded.get(plugin_type, {}):
            return cls._loaded[plugin_type][name_lower]
        
        # Check manual registrations
        if name_lower in cls._manual.get(plugin_type, {}):
            return cls._manual[plugin_type][name_lower]
        
        # Try to lazy load from entry point
        ep = cls._entry_points.get(plugin_type, {}).get(name_lower)
        if ep is not None:
            plugin_cls = cls._load_entry_point(ep, plugin_type, name_lower)
            if plugin_cls is not None:
                return plugin_cls
        
        return None
    
    @classmethod
    def _load_entry_point(
        cls,
        ep: "EntryPoint",
        plugin_type: str,
        name: str
    ) -> Optional[Type]:
        """
        Load a plugin from an entry point with version validation.
        
        Args:
            ep: The EntryPoint object
            plugin_type: Type of plugin
            name: Name of the plugin
            
        Returns:
            The loaded plugin class, or None on failure
        """
        try:
            plugin_cls = ep.load()
            
            # Check API version compatibility
            if not check_plugin_version(plugin_cls):
                version = getattr(plugin_cls, "strutex_plugin_version", "unknown")
                warnings.warn(
                    f"Plugin '{name}' has incompatible API version {version} "
                    f"(expected {PLUGIN_API_VERSION}). It may not work correctly.",
                    UserWarning
                )
            
            # Cache the loaded plugin
            if plugin_type not in cls._loaded:
                cls._loaded[plugin_type] = {}
            cls._loaded[plugin_type][name] = plugin_cls
            
            return plugin_cls
            
        except Exception as e:
            warnings.warn(
                f"Failed to load plugin '{name}' from entry point: {e}",
                UserWarning
            )
            return None
    
    @classmethod
    def list(cls, plugin_type: str) -> Dict[str, Type]:
        """
        List all plugins of a given type.
        
        Note: This loads all plugins of the type. Use list_names()
        for a lightweight listing without loading.
        
        Args:
            plugin_type: Type of plugin
            
        Returns:
            Dictionary mapping names to plugin classes
        """
        if not cls._discovered:
            cls.discover()
        
        result = {}
        
        # Get all names from entry points and manual registrations
        all_names = set()
        all_names.update(cls._entry_points.get(plugin_type, {}).keys())
        all_names.update(cls._manual.get(plugin_type, {}).keys())
        all_names.update(cls._loaded.get(plugin_type, {}).keys())
        
        # Load each plugin
        for name in all_names:
            plugin_cls = cls.get(plugin_type, name)
            if plugin_cls is not None:
                result[name] = plugin_cls
        
        return result
    
    @classmethod
    def get_sorted(cls, plugin_type: str, reverse: bool = True) -> List[Tuple[str, Type]]:
        """
        Get all plugins of a type sorted by priority.
        
        Useful for waterfall selection where you want to try
        higher-priority plugins first.
        
        Args:
            plugin_type: Type of plugin
            reverse: If True (default), higher priority first
            
        Returns:
            List of (name, class) tuples sorted by priority
        """
        plugins = cls.list(plugin_type)
        return sorted(
            plugins.items(),
            key=lambda x: getattr(x[1], 'priority', 50),
            reverse=reverse
        )
    
    @classmethod
    def list_names(cls, plugin_type: str) -> List[str]:
        """
        List names of all plugins of a given type without loading them.
        
        Args:
            plugin_type: Type of plugin
            
        Returns:
            List of plugin names
        """
        if not cls._discovered:
            cls.discover()
        
        names = set()
        names.update(cls._entry_points.get(plugin_type, {}).keys())
        names.update(cls._manual.get(plugin_type, {}).keys())
        names.update(cls._loaded.get(plugin_type, {}).keys())
        
        return sorted(names)
    
    @classmethod
    def list_types(cls) -> List[str]:
        """List all registered plugin types."""
        if not cls._discovered:
            cls.discover()
        
        types = set()
        types.update(cls._entry_points.keys())
        types.update(cls._manual.keys())
        types.update(cls._loaded.keys())
        
        return sorted(types)
    
    @classmethod
    def get_plugin_info(cls, plugin_type: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a plugin without necessarily loading it.
        
        Args:
            plugin_type: Type of plugin
            name: Name of the plugin
            
        Returns:
            Dict with plugin info, or None if not found
        """
        name_lower = name.lower()
        
        if not cls._discovered:
            cls.discover()
        
        # Check if loaded
        if name_lower in cls._loaded.get(plugin_type, {}):
            plugin_cls = cls._loaded[plugin_type][name_lower]
            return {
                "name": name_lower,
                "version": getattr(plugin_cls, "strutex_plugin_version", "unknown"),
                "priority": getattr(plugin_cls, "priority", 50),
                "cost": getattr(plugin_cls, "cost", 1.0),
                "capabilities": getattr(plugin_cls, "capabilities", []),
                "loaded": True,
                "healthy": cls._check_health(plugin_cls),
            }
        
        # Check entry point
        ep = cls._entry_points.get(plugin_type, {}).get(name_lower)
        if ep is not None:
            return {
                "name": name_lower,
                "entry_point": f"{ep.group}:{ep.name}",
                "loaded": False,
                "healthy": None,  # Unknown until loaded
            }
        
        return None
    
    @classmethod
    def _check_health(cls, plugin_cls: Type) -> bool:
        """Run health check on a plugin class."""
        try:
            if hasattr(plugin_cls, "health_check"):
                return plugin_cls.health_check()
            return True
        except Exception:
            return False
    
    @classmethod
    def clear(cls, plugin_type: Optional[str] = None) -> None:
        """
        Clear registered plugins.
        
        Args:
            plugin_type: If provided, only clear this type. Otherwise clear all.
        """
        if plugin_type:
            cls._entry_points.pop(plugin_type, None)
            cls._loaded.pop(plugin_type, None)
            cls._manual.pop(plugin_type, None)
        else:
            cls._entry_points.clear()
            cls._loaded.clear()
            cls._manual.clear()
            cls._discovered = False
    
    @classmethod
    def discover(cls, group_prefix: str = "strutex", force: bool = False) -> int:
        """
        Discover and register plugins from entry points.
        
        Scans for entry points matching the pattern:
        - strutex.providers
        - strutex.validators
        - strutex.postprocessors
        - strutex.security
        - etc.
        
        Entry points are stored for lazy loading - they are not imported
        until first use via get().
        
        Args:
            group_prefix: Entry point group prefix (default: "strutex")
            force: Force re-discovery even if already discovered
            
        Returns:
            Number of entry points discovered
            
        Example pyproject.toml:
            [project.entry-points."strutex.providers"]
            my_provider = "my_package:MyProvider"
        """
        if cls._discovered and not force:
            return sum(len(eps) for eps in cls._entry_points.values())
        
        discovered = 0
        
        # Get entry_points function
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points
        else:
            try:
                from importlib_metadata import entry_points
            except ImportError:
                cls._discovered = True
                return 0
        
        # Get all entry point groups
        try:
            all_eps = entry_points()
            
            # Get group names that match our prefix
            if hasattr(all_eps, 'groups'):
                # Python 3.12+ style
                groups = [g for g in all_eps.groups if g.startswith(f"{group_prefix}.")]
            elif hasattr(all_eps, 'keys'):
                # Python 3.9-3.11 style (dict-like)
                groups = [g for g in all_eps.keys() if g.startswith(f"{group_prefix}.")]
            else:
                groups = []
        except Exception:
            cls._discovered = True
            return 0
        
        for group in groups:
            # Extract plugin type from group name
            # e.g., "strutex.providers" -> "provider"
            plugin_type = group.replace(f"{group_prefix}.", "").rstrip("s")
            
            if plugin_type not in cls._entry_points:
                cls._entry_points[plugin_type] = {}
            
            try:
                # Get entry points for this group
                if hasattr(all_eps, 'select'):
                    eps = all_eps.select(group=group)
                else:
                    eps = all_eps.get(group, [])
                
                for ep in eps:
                    # Store entry point for lazy loading
                    cls._entry_points[plugin_type][ep.name.lower()] = ep
                    discovered += 1
                    
            except Exception:
                pass
        
        cls._discovered = True
        return discovered


def register(
    plugin_type: str,
    name: Optional[str] = None,
) -> Callable[[Type], Type]:
    """
    Decorator to register a plugin class at runtime.
    
    Use this decorator for:
    - Runtime/dynamic registration based on config
    - Prototyping plugins without packaging
    - Plugins in the same codebase (not installed separately)
    - Conditional loading based on environment or feature flags
    
    For distributable third-party plugin packages, use entry points
    in pyproject.toml instead.
    
    Args:
        plugin_type: Type of plugin (e.g., "provider", "security", "validator")
        name: Optional name. If not provided, uses lowercase class name.
        
    Usage:
        @register("provider")
        class MyProvider(Provider):
            ...
        
        @register("provider", name="custom_name")
        class AnotherProvider(Provider):
            ...
    
    See Also:
        Entry points in pyproject.toml for distributable packages:
        
            [project.entry-points."strutex.providers"]
            my_provider = "my_package:MyProvider"
    """
    def decorator(cls: Type) -> Type:
        plugin_name = name if name else cls.__name__.lower()
        PluginRegistry.register(plugin_type, plugin_name, cls)
        return cls
    
    return decorator


# Convenience decorators for each plugin type
def provider(name: Optional[str] = None) -> Callable[[Type], Type]:
    """Register a provider plugin. See `register` for details."""
    return register("provider", name)


def extractor(name: Optional[str] = None) -> Callable[[Type], Type]:
    """Register an extractor plugin. See `register` for details."""
    return register("extractor", name)


def validator(name: Optional[str] = None) -> Callable[[Type], Type]:
    """Register a validator plugin. See `register` for details."""
    return register("validator", name)


def postprocessor(name: Optional[str] = None) -> Callable[[Type], Type]:
    """Register a postprocessor plugin. See `register` for details."""
    return register("postprocessor", name)


def security(name: Optional[str] = None) -> Callable[[Type], Type]:
    """Register a security plugin. See `register` for details."""
    return register("security", name)
