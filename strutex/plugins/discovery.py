"""
Plugin discovery with caching.

Provides efficient plugin discovery by caching results based on
the installed Python packages. The cache is invalidated when
packages are installed or removed.

Example:
    >>> from strutex.plugins.discovery import PluginDiscovery
    >>> 
    >>> # Discover with caching
    >>> plugins = PluginDiscovery.discover()
    >>> 
    >>> # Force refresh
    >>> plugins = PluginDiscovery.discover(force_refresh=True)
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class PluginDiscovery:
    """
    Cached plugin discovery system.
    
    Caches discovery results based on a hash of installed distributions.
    This avoids expensive re-scanning of entry points on every import.
    
    The cache is stored in ~/.cache/strutex/plugins.json and is automatically
    invalidated when packages are installed or removed.
    """
    
    _cache_dir = Path.home() / ".cache" / "strutex"
    _cache_file = _cache_dir / "plugins.json"
    
    @classmethod
    def discover(
        cls,
        group_prefix: str = "strutex",
        force_refresh: bool = False
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Discover plugins with caching.
        
        Args:
            group_prefix: Entry point group prefix (default: "strutex")
            force_refresh: Skip cache and re-discover
            
        Returns:
            Dict mapping plugin types to lists of plugin info dicts
        """
        cache_key = cls._compute_venv_hash()
        
        # Try to load from cache
        if not force_refresh:
            cached = cls._load_cache()
            if cached is not None and cached.get("hash") == cache_key:
                return cached.get("plugins", {})
        
        # Discover fresh
        plugins = cls._discover_entry_points(group_prefix)
        
        # Save to cache
        cls._save_cache({
            "hash": cache_key,
            "group_prefix": group_prefix,
            "plugins": plugins,
        })
        
        return plugins
    
    @classmethod
    def _discover_entry_points(cls, group_prefix: str) -> Dict[str, List[Dict[str, str]]]:
        """Discover entry points from installed packages."""
        result: Dict[str, List[Dict[str, str]]] = {}
        
        # Get entry_points function
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points
        else:
            try:
                from importlib_metadata import entry_points
            except ImportError:
                return result
        
        try:
            all_eps = entry_points()
            
            # Get group names
            if hasattr(all_eps, 'groups'):
                groups = [g for g in all_eps.groups if g.startswith(f"{group_prefix}.")]
            elif hasattr(all_eps, 'keys'):
                groups = [g for g in all_eps.keys() if g.startswith(f"{group_prefix}.")]
            else:
                groups = []
        except Exception:
            return result
        
        for group in groups:
            # Extract plugin type from group name
            plugin_type = group.replace(f"{group_prefix}.", "").rstrip("s")
            
            if plugin_type not in result:
                result[plugin_type] = []
            
            try:
                if hasattr(all_eps, 'select'):
                    eps = all_eps.select(group=group)
                else:
                    eps = all_eps.get(group, [])
                
                for ep in eps:
                    result[plugin_type].append({
                        "name": ep.name,
                        "value": ep.value,
                        "group": group,
                    })
            except Exception:
                pass
        
        return result
    
    @classmethod
    def _compute_venv_hash(cls) -> str:
        """
        Compute a hash of installed distributions.
        
        This is used to detect when packages have changed and
        the cache needs to be invalidated.
        
        Returns:
            A 16-character hex hash
        """
        try:
            if sys.version_info >= (3, 10):
                from importlib.metadata import distributions
            else:
                from importlib_metadata import distributions
            
            # Get sorted list of installed packages
            dist_info = sorted(f"{d.name}=={d.version}" for d in distributions())
            
            # Hash the list
            content = "\n".join(dist_info).encode("utf-8")
            return hashlib.sha256(content).hexdigest()[:16]
            
        except Exception:
            # If we can't compute hash, always re-discover
            return ""
    
    @classmethod
    def _load_cache(cls) -> Optional[Dict[str, Any]]:
        """Load the cache file if it exists."""
        try:
            if cls._cache_file.exists():
                return json.loads(cls._cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return None
    
    @classmethod
    def _save_cache(cls, data: Dict[str, Any]) -> None:
        """Save data to the cache file."""
        try:
            cls._cache_dir.mkdir(parents=True, exist_ok=True)
            cls._cache_file.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8"
            )
        except Exception:
            # Cache write failure is non-fatal
            pass
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the discovery cache."""
        try:
            if cls._cache_file.exists():
                cls._cache_file.unlink()
        except Exception:
            pass
    
    @classmethod
    def get_cache_info(cls) -> Optional[Dict[str, Any]]:
        """
        Get information about the current cache state.
        
        Returns:
            Dict with cache info, or None if no cache exists
        """
        cached = cls._load_cache()
        if cached is None:
            return None
        
        current_hash = cls._compute_venv_hash()
        
        return {
            "cache_file": str(cls._cache_file),
            "cached_hash": cached.get("hash"),
            "current_hash": current_hash,
            "is_valid": cached.get("hash") == current_hash,
            "plugin_count": sum(
                len(plugins) for plugins in cached.get("plugins", {}).values()
            ),
        }
