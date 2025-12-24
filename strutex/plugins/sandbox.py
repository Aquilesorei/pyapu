"""
Sandbox for safely probing untrusted plugins.

Provides subprocess-based plugin probing to extract metadata without
importing potentially dangerous code into the main process.

Example:
    >>> from strutex.plugins.sandbox import probe_plugin_metadata
    >>> 
    >>> info = probe_plugin_metadata("strutex.providers", "my_provider")
    >>> print(info)
    {'name': 'my_provider', 'version': '1.0', 'healthy': True, ...}
"""

import json
import subprocess
import sys
from typing import Any, Dict, Optional


# Script template for probing plugins in subprocess
_PROBE_SCRIPT = '''
import json
import sys

def probe():
    try:
        # Get entry point
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points
        else:
            from importlib_metadata import entry_points
        
        all_eps = entry_points()
        
        # Find the entry point
        if hasattr(all_eps, 'select'):
            eps = list(all_eps.select(group="{group}"))
        else:
            eps = list(all_eps.get("{group}", []))
        
        ep = None
        for e in eps:
            if e.name.lower() == "{name}".lower():
                ep = e
                break
        
        if ep is None:
            print(json.dumps({{"error": "Entry point not found", "healthy": False}}))
            return
        
        # Load the plugin class
        cls = ep.load()
        
        # Extract metadata
        result = {{
            "name": ep.name,
            "version": getattr(cls, "strutex_plugin_version", "unknown"),
            "priority": getattr(cls, "priority", 50),
            "cost": getattr(cls, "cost", 1.0),
            "capabilities": list(getattr(cls, "capabilities", [])),
            "module": cls.__module__,
            "class_name": cls.__name__,
        }}
        
        # Run health check if available
        if hasattr(cls, "health_check"):
            try:
                result["healthy"] = bool(cls.health_check())
            except Exception as e:
                result["healthy"] = False
                result["health_error"] = str(e)
        else:
            result["healthy"] = True
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({{"error": str(e), "healthy": False}}))

probe()
'''


def probe_plugin_metadata(
    group: str,
    name: str,
    timeout: float = 5.0,
    python_executable: Optional[str] = None
) -> Dict[str, Any]:
    """
    Probe a plugin's metadata in a subprocess.
    
    This safely extracts plugin metadata without importing the plugin
    into the main process. Useful for untrusted or heavy plugins.
    
    Args:
        group: Entry point group (e.g., "strutex.providers")
        name: Plugin name within the group
        timeout: Maximum time to wait for probe (seconds)
        python_executable: Python interpreter to use (default: same as current)
        
    Returns:
        Dict with plugin metadata:
        - name: Plugin name
        - version: API version string
        - priority: Priority value
        - cost: Cost value
        - capabilities: List of capabilities
        - healthy: Whether health check passed
        - error: Error message if probe failed
        
    Example:
        >>> info = probe_plugin_metadata("strutex.providers", "gemini")
        >>> if info.get("healthy"):
        ...     print(f"Plugin {info['name']} v{info['version']} is ready")
    """
    python = python_executable or sys.executable
    script = _PROBE_SCRIPT.format(group=group, name=name)
    
    try:
        result = subprocess.run(
            [python, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=None,  # Use current environment
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        else:
            return {
                "name": name,
                "healthy": False,
                "error": result.stderr.strip() or "Unknown error",
            }
            
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "healthy": False,
            "error": f"Probe timed out after {timeout}s",
        }
    except json.JSONDecodeError as e:
        return {
            "name": name,
            "healthy": False,
            "error": f"Invalid JSON response: {e}",
        }
    except Exception as e:
        return {
            "name": name,
            "healthy": False,
            "error": str(e),
        }


def probe_all_plugins(
    group: str,
    timeout_per_plugin: float = 5.0
) -> Dict[str, Dict[str, Any]]:
    """
    Probe all plugins in an entry point group.
    
    Args:
        group: Entry point group (e.g., "strutex.providers")
        timeout_per_plugin: Timeout for each plugin probe
        
    Returns:
        Dict mapping plugin names to their metadata
    """
    results = {}
    
    # First, get list of plugins without loading
    try:
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points
        else:
            from importlib_metadata import entry_points
        
        all_eps = entry_points()
        
        if hasattr(all_eps, 'select'):
            eps = list(all_eps.select(group=group))
        else:
            eps = list(all_eps.get(group, []))
        
        for ep in eps:
            results[ep.name] = probe_plugin_metadata(
                group, ep.name, timeout_per_plugin
            )
            
    except Exception as e:
        # Return error for the group
        return {"_error": {"error": str(e), "healthy": False}}
    
    return results


def is_plugin_safe(
    group: str,
    name: str,
    timeout: float = 5.0
) -> bool:
    """
    Quick check if a plugin is safe to load.
    
    Returns True if the plugin can be probed successfully and
    passes its health check.
    
    Args:
        group: Entry point group
        name: Plugin name
        timeout: Probe timeout
        
    Returns:
        True if plugin appears safe to load
    """
    info = probe_plugin_metadata(group, name, timeout)
    return info.get("healthy", False)
