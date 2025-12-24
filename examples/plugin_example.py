#!/usr/bin/env python3
"""
Plugin System v2 Example.

Demonstrates:
- Auto-registration via inheritance
- Plugin API versioning and priorities
- Class arguments for customization (name=, priority=, register=)
- Using decorators for aliases
- Lazy loading from entry points
- Protocol-based type checking
- Pluggy hooks for pipeline extension
"""

import os
import sys
import warnings

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyapu.plugins import (
    PluginRegistry,
    register,
    Provider,
    Extractor,
    Validator,
    ValidationResult,
    Postprocessor,
    # v2 additions
    PLUGIN_API_VERSION,
    ProviderProtocol,
    check_plugin_version,
    hookimpl,
    register_hook_plugin,
    call_hook,
)
from pyapu.types import Schema


def demo_v2_plugin_attributes():
    """Demonstrate new v2 plugin attributes."""
    print("=" * 60)
    print("PLUGIN SYSTEM v2 - API VERSION & PRIORITY")
    print("=" * 60)
    
    print(f"\nCurrent API Version: {PLUGIN_API_VERSION}")
    
    # Check built-in provider
    PluginRegistry.discover()
    gemini = PluginRegistry.get("provider", "gemini")
    
    if gemini:
        print(f"\nGeminiProvider attributes:")
        print(f"  pyapu_plugin_version: {gemini.pyapu_plugin_version}")
        print(f"  priority: {gemini.priority}")
        print(f"  cost: {gemini.cost}")
        print(f"  capabilities: {gemini.capabilities}")
        print(f"  health_check(): {gemini.health_check()}")
    
    # Version compatibility check
    print(f"\nVersion compatible: {check_plugin_version(gemini)}")


def demo_lazy_loading():
    """Demonstrate lazy loading from entry points."""
    print("\n" + "=" * 60)
    print("LAZY LOADING FROM ENTRY POINTS")
    print("=" * 60)
    
    PluginRegistry.clear()
    PluginRegistry.discover()
    
    # Get plugin info without loading
    info = PluginRegistry.get_plugin_info("provider", "gemini")
    if info:
        print(f"\nBefore get() - loaded: {info.get('loaded', False)}")
        
        # Now load it
        cls = PluginRegistry.get("provider", "gemini")
        
        # Check again
        info = PluginRegistry.get_plugin_info("provider", "gemini")
        print(f"After get() - loaded: {info.get('loaded', True)}")
        print(f"Plugin info: {info}")
    else:
        print("\nNo entry point plugins discovered (gemini not installed as package)")
        print("This is expected when running from source.")


def demo_plugin_listing():
    """Demonstrate plugin listing methods."""
    print("\n" + "=" * 60)
    print("PLUGIN LISTING (CLI: pyapu plugins list)")
    print("=" * 60)
    
    PluginRegistry.discover()
    
    # List all types
    print(f"\nPlugin types: {PluginRegistry.list_types()}")
    
    # List names without loading
    print(f"Provider names: {PluginRegistry.list_names('provider')}")
    
    # Get detailed info
    for name in PluginRegistry.list_names("provider"):
        info = PluginRegistry.get_plugin_info("provider", name)
        status = "●" if info.get("loaded") else "○"
        version = info.get("version", "?")
        priority = info.get("priority", "?")
        print(f"  {status} {name:<20} v{version:<8} priority: {priority}")


def demo_auto_registration():
    """Demonstrate auto-registration via inheritance."""
    print("\n" + "=" * 60)
    print("AUTO-REGISTRATION VIA INHERITANCE")
    print("=" * 60)
    
    PluginRegistry.clear()
    
    # Simply inherit from Provider - auto-registered as "mockv2provider"
    class MockV2Provider(Provider):
        """A v2-compliant mock provider - auto-registered!"""
        
        # Optional overrides (defaults inherited from base class)
        priority = 75  # Higher priority = preferred in waterfall
        cost = 0.5     # Lower cost = cheaper option
        capabilities = ["mock", "testing", "batch"]
        
        def __init__(self, response_data: dict = None):
            self.response_data = response_data or {"mock": True}
        
        def process(self, file_path, prompt, schema, mime_type, **kwargs):
            return self.response_data
        
        @classmethod
        def health_check(cls) -> bool:
            return True
    
    print(f"\nAuto-registered: {PluginRegistry.list_names('provider')}")
    print(f"MockV2Provider found: {PluginRegistry.get('provider', 'mockv2provider') is not None}")
    
    # Customize with class arguments
    print("\n--- Custom Name ---")
    
    class FastProvider(Provider, name="fast"):
        """Registered as 'fast' with custom priority"""
        priority = 90  # Priority is a class attribute, not a class argument
        cost = 0.1
        capabilities = ["fast"]
        
        def process(self, *args, **kwargs):
            return {"fast": True}
    
    print(f"Registered as 'fast': {PluginRegistry.get('provider', 'fast') is not None}")
    print(f"Priority: {FastProvider.priority}")
    
    # Opt-out with register=False
    print("\n--- Opt-out of Registration ---")
    
    class BasePdfProvider(Provider, register=False):
        """NOT registered - intermediate base class"""
        def common_pdf_logic(self):
            return "shared logic"
    
    class AdobeProvider(BasePdfProvider):
        """Registered as 'adobeprovider'"""
        def process(self, *args, **kwargs):
            return self.common_pdf_logic()
    
    print(f"BasePdfProvider registered: {PluginRegistry.get('provider', 'basepdfprovider') is not None}")
    print(f"AdobeProvider registered: {PluginRegistry.get('provider', 'adobeprovider') is not None}")
    
    # Verify protocol compliance
    print("\n--- Protocol Compliance ---")
    provider = MockV2Provider()
    is_compliant = isinstance(provider, ProviderProtocol)
    print(f"Protocol compliant: {is_compliant}")
    print(f"Version check: {check_plugin_version(MockV2Provider)}")


def demo_priority_sorting():
    """Demonstrate priority-based plugin ordering."""
    print("\n" + "=" * 60)
    print("PRIORITY-BASED ORDERING")
    print("=" * 60)
    
    PluginRegistry.clear()
    
    class LowPriorityProvider(Provider):
        pyapu_plugin_version = "1.0"
        priority = 20
        cost = 0.1
        capabilities = []
        def process(self, *args, **kwargs): pass
    
    class MediumPriorityProvider(Provider):
        pyapu_plugin_version = "1.0"
        priority = 50
        cost = 1.0
        capabilities = []
        def process(self, *args, **kwargs): pass
    
    class HighPriorityProvider(Provider):
        pyapu_plugin_version = "1.0"
        priority = 80
        cost = 2.0
        capabilities = []
        def process(self, *args, **kwargs): pass
    
    PluginRegistry.register("provider", "low", LowPriorityProvider)
    PluginRegistry.register("provider", "medium", MediumPriorityProvider)
    PluginRegistry.register("provider", "high", HighPriorityProvider)
    
    # Get all and sort by priority
    providers = PluginRegistry.list("provider")
    sorted_providers = sorted(
        providers.items(),
        key=lambda x: x[1].priority,
        reverse=True  # Higher priority first
    )
    
    print("\nProviders sorted by priority (high to low):")
    for name, cls in sorted_providers:
        print(f"  {name}: priority={cls.priority}, cost={cls.cost}")


def demo_hooks():
    """Demonstrate pluggy hooks for pipeline extension."""
    print("\n" + "=" * 60)
    print("PLUGGY HOOKS")
    print("=" * 60)
    
    class LoggingPlugin:
        """Plugin that logs pre/post processing."""
        
        @hookimpl
        def pyapu_pre_process(self, file_path, prompt, schema, mime_type, context):
            import time
            context["start_time"] = time.time()
            print(f"  [Hook] Pre-process: {file_path}")
            return None  # Don't modify inputs
        
        @hookimpl
        def pyapu_post_process(self, result, context):
            import time
            elapsed = time.time() - context.get("start_time", 0)
            print(f"  [Hook] Post-process: elapsed={elapsed:.3f}s")
            return None  # Don't modify result
    
    try:
        # Register hook plugin
        plugin = LoggingPlugin()
        register_hook_plugin(plugin)
        
        # Call hooks manually (normally done by DocumentProcessor)
        context = {}
        call_hook("pyapu_pre_process",
            file_path="test.pdf",
            prompt="Extract data",
            schema=None,
            mime_type="application/pdf",
            context=context
        )
        
        import time
        time.sleep(0.1)  # Simulate processing
        
        call_hook("pyapu_post_process",
            result={"extracted": True},
            context=context
        )
        
        print("\n  Hooks executed successfully!")
        
    except RuntimeError as e:
        print(f"\n  Note: {e}")


def demo_aliases_with_decorator():
    """Demonstrate using decorators to create aliases."""
    print("\n" + "=" * 60)
    print("DECORATORS FOR ALIASES")
    print("=" * 60)
    
    PluginRegistry.clear()
    
    print("\nUse decorators to register the same plugin under multiple names:")
    
    # A provider registered via inheritance AND decorator
    @register("provider", name="premium")
    class PremiumProvider(Provider, name="pro"):
        """Accessible as both 'pro' AND 'premium'"""
        priority = 95
        cost = 2.0
        capabilities = ["premium"]
        
        def process(self, *args, **kwargs):
            return {"premium": True}
    
    print(f"\nRegistered names: {PluginRegistry.list_names('provider')}")
    print(f"'pro' found: {PluginRegistry.get('provider', 'pro') is not None}")
    print(f"'premium' found: {PluginRegistry.get('provider', 'premium') is not None}")
    print(f"Same class? {PluginRegistry.get('provider', 'pro') is PluginRegistry.get('provider', 'premium')}")


def demo_cli_commands():
    """Show available CLI commands."""
    print("\n" + "=" * 60)
    print("CLI COMMANDS (pyapu plugins ...)")
    print("=" * 60)
    
    print("""
Available commands:

  pyapu plugins list
      List all discovered plugins with health status
      
  pyapu plugins list --type provider
      Filter by plugin type
      
  pyapu plugins list --json
      Output as JSON for scripting
      
  pyapu plugins info gemini --type provider
      Show detailed info for a specific plugin
      
  pyapu plugins refresh
      Re-scan entry points and refresh cache
      
  pyapu plugins cache
      Show cache status
      
  pyapu plugins cache --clear
      Clear the discovery cache
""")


def demo_custom_validator_v2():
    """Demonstrate a v2-compliant validator with auto-registration."""
    print("\n" + "=" * 60)
    print("V2-COMPLIANT VALIDATOR (Auto-Registered)")
    print("=" * 60)
    
    PluginRegistry.clear('validator')
    
    # Auto-registered as 'invoicevalidator'
    class InvoiceValidator(Validator):
        """Validates invoice data with business rules - auto-registered!"""
        priority = 60
        
        def validate(self, data, schema=None):
            issues = []
            
            if not data.get("invoice_number"):
                issues.append("Missing invoice number")
            
            total = data.get("total", 0)
            if total <= 0:
                issues.append(f"Invalid total: {total}")
            
            items = data.get("items", [])
            if items:
                items_total = sum(item.get("total", 0) for item in items)
                if abs(items_total - total) > 0.01:
                    issues.append(f"Sum mismatch: items={items_total}, total={total}")
            
            return ValidationResult(
                valid=len(issues) == 0,
                data=data,
                issues=issues
            )
    
    print(f"\nAuto-registered validators: {PluginRegistry.list_names('validator')}")
    
    validator = InvoiceValidator()
    
    # Test valid data
    valid_data = {
        "invoice_number": "INV-001",
        "total": 100.00,
        "items": [{"total": 60.00}, {"total": 40.00}]
    }
    result = validator.validate(valid_data)
    print(f"\nValid data: {result.valid}")
    
    # Test invalid data
    invalid_data = {"total": -50}
    result = validator.validate(invalid_data)
    print(f"Invalid data: {result.valid}, Issues: {result.issues}")


if __name__ == "__main__":
    demo_v2_plugin_attributes()
    demo_lazy_loading()
    demo_plugin_listing()
    demo_auto_registration()
    demo_priority_sorting()
    demo_hooks()
    demo_aliases_with_decorator()
    demo_cli_commands()
    demo_custom_validator_v2()
    
    print("\n" + "=" * 60)
    print("Done! See docs for more: poetry run mkdocs serve")
    print("=" * 60)
