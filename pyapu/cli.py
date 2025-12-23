"""
Command-line interface for pyapu.

Provides commands for plugin management and document processing.

Usage:
    pyapu plugins list
    pyapu plugins list --type provider --json
    pyapu plugins info gemini --type provider

Requires the 'cli' extra:
    pip install pyapu[cli]
"""

import json
import sys
from typing import Optional

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    click = None  # type: ignore


def _check_click():
    """Raise helpful error if click is not installed."""
    if not CLICK_AVAILABLE:
        print("Error: The 'click' package is required for CLI commands.")
        print("Install with: pip install pyapu[cli]")
        sys.exit(1)


# Only define CLI if click is available
if CLICK_AVAILABLE:
    from .plugins import PluginRegistry
    from .plugins.discovery import PluginDiscovery


@click.group()
@click.version_option()
def cli():
    """pyapu - Python AI PDF Utilities.
    
    Extract structured JSON from documents using LLMs.
    """
    pass


@cli.group()
def plugins():
    """Plugin management commands."""
    pass


@plugins.command("list")
@click.option(
    "--type", "-t", "plugin_type",
    help="Filter by plugin type (e.g., provider, validator)"
)
@click.option(
    "--json", "as_json", is_flag=True,
    help="Output as JSON"
)
@click.option(
    "--loaded-only", is_flag=True,
    help="Only show already-loaded plugins"
)
def list_plugins(
    plugin_type: Optional[str],
    as_json: bool,
    loaded_only: bool
):
    """List all discovered plugins.
    
    Shows plugin name, version, priority, and health status.
    
    Examples:
    
        pyapu plugins list
        
        pyapu plugins list --type provider
        
        pyapu plugins list --json
    """
    # Ensure discovery has run
    PluginRegistry.discover()
    
    # Collect plugin data
    if plugin_type:
        types_to_show = [plugin_type]
    else:
        types_to_show = PluginRegistry.list_types()
    
    output_data = {}
    
    for ptype in types_to_show:
        names = PluginRegistry.list_names(ptype)
        plugins_info = []
        
        for name in names:
            info = PluginRegistry.get_plugin_info(ptype, name)
            if info:
                if loaded_only and not info.get("loaded", False):
                    continue
                plugins_info.append(info)
        
        if plugins_info:
            output_data[ptype] = plugins_info
    
    if as_json:
        click.echo(json.dumps(output_data, indent=2, default=str))
    else:
        if not output_data:
            click.echo("No plugins found.")
            return
        
        for ptype, plugins_list in output_data.items():
            click.secho(f"\n{ptype.upper()}S", bold=True, fg="cyan")
            click.echo("-" * 40)
            
            for info in plugins_list:
                # Health indicator
                if info.get("healthy") is True:
                    health = click.style("✓", fg="green")
                elif info.get("healthy") is False:
                    health = click.style("✗", fg="red")
                else:
                    health = click.style("?", fg="yellow")
                
                # Loaded indicator
                loaded = "●" if info.get("loaded") else "○"
                loaded = click.style(loaded, fg="blue" if info.get("loaded") else "white")
                
                # Version and priority
                version = info.get("version", "?")
                priority = info.get("priority", "?")
                
                click.echo(f"  {health} {loaded} {info['name']:<20} v{version:<8} priority: {priority}")
                
                # Show capabilities if present
                capabilities = info.get("capabilities", [])
                if capabilities:
                    caps_str = ", ".join(capabilities)
                    click.echo(f"       └─ capabilities: {caps_str}")


@plugins.command("info")
@click.argument("name")
@click.option(
    "--type", "-t", "plugin_type", required=True,
    help="Plugin type (e.g., provider, validator)"
)
@click.option(
    "--json", "as_json", is_flag=True,
    help="Output as JSON"
)
def plugin_info(name: str, plugin_type: str, as_json: bool):
    """Show detailed information about a specific plugin.
    
    Examples:
    
        pyapu plugins info gemini --type provider
    """
    PluginRegistry.discover()
    
    info = PluginRegistry.get_plugin_info(plugin_type, name)
    
    if info is None:
        click.echo(f"Plugin '{name}' of type '{plugin_type}' not found.", err=True)
        sys.exit(1)
    
    if as_json:
        click.echo(json.dumps(info, indent=2, default=str))
    else:
        click.secho(f"\nPlugin: {info['name']}", bold=True)
        click.echo("-" * 40)
        
        for key, value in info.items():
            if key == "name":
                continue
            
            # Format lists nicely
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value) if value else "(none)"
            
            click.echo(f"  {key:<15}: {value}")


@plugins.command("refresh")
def refresh_plugins():
    """Refresh plugin discovery cache.
    
    Clears the discovery cache and re-scans for plugins.
    """
    PluginDiscovery.clear_cache()
    PluginRegistry.clear()
    
    count = PluginRegistry.discover(force=True)
    
    click.echo(f"Discovered {count} plugin(s).")
    
    # Show cache info
    cache_info = PluginDiscovery.get_cache_info()
    if cache_info:
        click.echo(f"Cache saved to: {cache_info['cache_file']}")


@plugins.command("cache")
@click.option("--clear", is_flag=True, help="Clear the discovery cache")
def cache_command(clear: bool):
    """Manage the plugin discovery cache."""
    if clear:
        PluginDiscovery.clear_cache()
        click.echo("Cache cleared.")
        return
    
    # Show cache info
    info = PluginDiscovery.get_cache_info()
    
    if info is None:
        click.echo("No cache file exists.")
        return
    
    click.echo(f"Cache file: {info['cache_file']}")
    click.echo(f"Cache valid: {info['is_valid']}")
    click.echo(f"Cached plugins: {info['plugin_count']}")
    
    if not info['is_valid']:
        click.echo(f"\nCache is stale (packages have changed).")
        click.echo("Run 'pyapu plugins refresh' to update.")


def main():
    """Entry point for the CLI."""
    _check_click()
    cli()


if __name__ == "__main__":
    main()
