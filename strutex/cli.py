"""
Command-line interface for strutex.

Provides commands for plugin management and document processing.

Usage:
    strutex plugins list
    strutex plugins list --type provider --json
    strutex plugins info gemini --type provider

Requires the 'cli' extra:
    pip install strutex[cli]
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
        print("Install with: pip install strutex[cli]")
        sys.exit(1)


# Only define CLI if click is available
if CLICK_AVAILABLE:
    from .plugins import PluginRegistry
    from .plugins.discovery import PluginDiscovery


@click.group()
@click.version_option()
def cli():
    """strutex - Python AI PDF Utilities.
    
    Extract structured JSON from documents using LLMs.
    """
    pass


@cli.command("run")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output file path (default: stdout)")
@click.option(
    "--format", "output_format",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run_extraction(
    config_file: str,
    output: Optional[str],
    output_format: str,
    verbose: bool
):
    """Run document extraction from a YAML config file.
    
    The config file should contain:
    
    \b
        provider: gemini          # Provider name
        model: gemini-2.5-flash   # Model name (optional)
        file: document.pdf        # File to process
        prompt: "Extract..."      # Extraction prompt
        schema:                   # Expected output schema
          type: object
          properties:
            title:
              type: string
    
    Examples:
    
        strutex run config.yaml
        
        strutex run config.yaml -o result.json
        
        strutex run config.yaml --format yaml -v
    """
    import os
    
    try:
        import yaml  # type: ignore
    except ImportError:
        click.echo("Error: PyYAML is required for config files.", err=True)
        click.echo("Install with: pip install pyyaml", err=True)
        sys.exit(1)
    
    # Load config
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    
    if not config:
        click.echo("Error: Empty config file.", err=True)
        sys.exit(1)
    
    # Validate required fields
    required = ["file", "prompt"]
    missing = [f for f in required if f not in config]
    if missing:
        click.echo(f"Error: Missing required fields: {', '.join(missing)}", err=True)
        sys.exit(1)
    
    file_path = config["file"]
    if not os.path.exists(file_path):
        click.echo(f"Error: File not found: {file_path}", err=True)
        sys.exit(1)
    
    # Import processor
    from . import DocumentProcessor
    from .types import Schema
    
    # Build schema if provided
    schema = None
    if "schema" in config:
        schema = Schema.from_dict(config["schema"])
    
    # Create processor
    provider = config.get("provider", "gemini")
    model = config.get("model")
    
    if verbose:
        click.echo(f"Provider: {provider}")
        if model:
            click.echo(f"Model: {model}")
        click.echo(f"File: {file_path}")
    
    try:
        processor = DocumentProcessor(
            provider=provider,
            model_name=model
        )
        
        result = processor.process(
            file_path=file_path,
            prompt=config["prompt"],
            schema=schema
        )
        
        # Format output
        if output_format == "yaml":
            output_str = yaml.dump(result, default_flow_style=False, allow_unicode=True)
        else:
            output_str = json.dumps(result, indent=2, ensure_ascii=False)
        
        # Write output
        if output:
            with open(output, "w") as f:
                f.write(output_str)
            if verbose:
                click.echo(f"Output written to: {output}")
        else:
            click.echo(output_str)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command("example")
@click.argument("name", required=False)
@click.option("--list", "-l", "list_examples", is_flag=True, help="List available examples")
def run_example(name: Optional[str], list_examples: bool):
    """Run a bundled example script.
    
    Run examples from the strutex examples directory.
    
    Examples:
    
        strutex example --list
        
        strutex example invoice_extraction_demo
        
        strutex example invoice_extraction_demo.py
    """
    import os
    import subprocess
    
    # Find examples directory
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    examples_dir = os.path.join(package_dir, "examples")
    
    # Check if examples exist (installed from source)
    if not os.path.exists(examples_dir):
        # Try relative to current working directory
        examples_dir = os.path.join(os.getcwd(), "examples")
    
    if not os.path.exists(examples_dir):
        click.echo("Error: Examples directory not found.", err=True)
        click.echo("Examples are available when running from source.", err=True)
        sys.exit(1)
    
    # List examples
    if list_examples or name is None:
        click.secho("\nAvailable Examples", bold=True, fg="cyan")
        click.echo("-" * 40)
        
        examples = sorted([
            f for f in os.listdir(examples_dir) 
            if f.endswith(".py") and not f.startswith("__")
        ])
        
        for example in examples:
            basename = example.replace(".py", "")
            click.echo(f"  • {basename}")
        
        click.echo(f"\nRun with: strutex example <name>")
        return
    
    # Normalize name
    if not name.endswith(".py"):
        name = f"{name}.py"
    
    example_path = os.path.join(examples_dir, name)
    
    if not os.path.exists(example_path):
        click.echo(f"Error: Example '{name}' not found.", err=True)
        click.echo(f"Run 'strutex example --list' to see available examples.", err=True)
        sys.exit(1)
    
    click.secho(f"Running: {name}", fg="cyan")
    click.echo("-" * 40)
    
    # Run the example with PYTHONPATH set
    env = os.environ.copy()
    env["PYTHONPATH"] = package_dir + os.pathsep + env.get("PYTHONPATH", "")
    
    result = subprocess.run(
        [sys.executable, example_path],
        env=env,
        cwd=examples_dir
    )
    
    sys.exit(result.returncode)


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
    
        strutex plugins list
        
        strutex plugins list --type provider
        
        strutex plugins list --json
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
    
        strutex plugins info gemini --type provider
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
        click.echo("Run 'strutex plugins refresh' to update.")


@cli.group()
def prompt():
    """Prompt builder commands."""
    pass


@prompt.command("build")
@click.option(
    "--persona", "-p",
    default="You are a highly accurate AI Data Extraction Assistant.",
    help="System persona for the prompt."
)
@click.option(
    "--rule", "-r",
    multiple=True,
    help="General rule (can be used multiple times)."
)
@click.option(
    "--field", "-f",
    multiple=True,
    help="Field rule as 'name:rule' or 'name:rule:critical' (can be used multiple times)."
)
@click.option(
    "--output", "-o",
    multiple=True,
    help="Output guideline (can be used multiple times)."
)
@click.option(
    "--from-schema", "-s",
    type=click.Path(exists=True),
    help="Python file with Pydantic schema to auto-generate from."
)
@click.option(
    "--schema-class", "-c",
    default=None,
    help="Class name to use from schema file (defaults to first BaseModel found)."
)
@click.option(
    "--save", type=click.Path(),
    help="Save prompt to file."
)
def build_prompt(persona, rule, field, output, from_schema, schema_class, save):
    """
    Build a structured prompt interactively or from options.
    
    Examples:
    
    \b
        # Build with options
        strutex prompt build -r "Use ISO dates" -r "No guessing" \\
            -f "total:Final amount due:critical" -f "vendor:Company name"
        
    \b
        # Generate from Pydantic schema
        strutex prompt build --from-schema models.py --schema-class Invoice
        
    \b    
        # Save to file
        strutex prompt build -r "Extract all data" -o prompt.txt
    """
    from .prompts import StructuredPrompt
    
    # Create prompt builder
    builder = StructuredPrompt(persona=persona)
    
    # Load from schema if provided
    if from_schema:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("schema_module", from_schema)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the schema class
            from pydantic import BaseModel
            schema_cls = None
            
            if schema_class:
                schema_cls = getattr(module, schema_class, None)
                if schema_cls is None:
                    click.echo(f"Error: Class '{schema_class}' not found in {from_schema}", err=True)
                    sys.exit(1)
            else:
                # Find first BaseModel subclass
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
                        schema_cls = obj
                        break
            
            if schema_cls:
                click.echo(f"Generating from schema: {schema_cls.__name__}")
                builder = StructuredPrompt.from_schema(schema_cls, persona=persona)
            else:
                click.echo(f"Error: No Pydantic BaseModel found in {from_schema}", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"Error loading schema: {e}", err=True)
            sys.exit(1)
    
    # Add general rules
    for r in rule:
        builder.add_general_rule(r)
    
    # Add field rules
    for f in field:
        parts = f.split(":")
        if len(parts) >= 2:
            field_name = parts[0]
            field_rule = parts[1]
            critical = len(parts) > 2 and parts[2].lower() == "critical"
            builder.add_field_rule(field_name, field_rule, critical=critical)
        else:
            click.echo(f"Warning: Invalid field format '{f}', expected 'name:rule'", err=True)
    
    # Add output guidelines
    for o in output:
        builder.add_output_guideline(o)
    
    # Compile and output
    compiled = builder.compile()
    
    if save:
        with open(save, "w") as fp:
            fp.write(compiled)
        click.echo(f"Prompt saved to: {save}")
    else:
        click.echo(compiled)


@prompt.command("interactive")
def build_prompt_interactive():
    """
    Build a prompt interactively with guided questions.
    
    Example:
    
        strutex prompt interactive
    """
    from .prompts import StructuredPrompt
    
    click.echo("=== Strutex Prompt Builder ===\n")
    
    # Get persona
    persona = click.prompt(
        "Persona (press Enter for default)",
        default="You are a highly accurate AI Data Extraction Assistant."
    )
    
    builder = StructuredPrompt(persona=persona)
    
    # General rules
    click.echo("\n--- General Rules ---")
    click.echo("Enter general rules (empty line to finish):")
    while True:
        rule = click.prompt("Rule", default="", show_default=False)
        if not rule:
            break
        builder.add_general_rule(rule)
    
    # Field rules
    click.echo("\n--- Field Rules ---")
    click.echo("Enter field rules (empty field name to finish):")
    while True:
        field_name = click.prompt("Field name", default="", show_default=False)
        if not field_name:
            break
        field_rule = click.prompt(f"  Rule for '{field_name}'")
        critical = click.confirm(f"  Mark as critical?", default=False)
        builder.add_field_rule(field_name, field_rule, critical=critical)
    
    # Output guidelines
    click.echo("\n--- Output Guidelines ---")
    click.echo("Enter output guidelines (empty line to finish):")
    while True:
        guideline = click.prompt("Guideline", default="", show_default=False)
        if not guideline:
            break
        builder.add_output_guideline(guideline)
    
    # Show result
    click.echo("\n=== Generated Prompt ===\n")
    compiled = builder.compile()
    click.echo(compiled)
    
    # Offer to save
    if click.confirm("\nSave to file?", default=False):
        path = click.prompt("File path", type=str)
        with open(path, "w") as fp:
            fp.write(compiled)
        click.echo(f"Saved to: {path}")


def main():
    """Entry point for the CLI."""
    _check_click()
    cli()


if __name__ == "__main__":
    main()
