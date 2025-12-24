"""
Tests for strutex v0.3.0 Plugin System v2 features.

Tests:
- Lazy loading
- Entry point discovery
- Priority-based sorting
- Protocol types
- Hooks system
- Discovery caching
- Sandbox probing
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex.plugins import (
    PluginRegistry,
    Provider,
    Validator,
    Postprocessor,
    PLUGIN_API_VERSION,
    ProviderProtocol,
    ValidatorProtocol,
    check_plugin_version,
    validate_plugin_protocol,
)
from strutex.plugins.hooks import (
    hookimpl,
    get_plugin_manager,
    register_hook_plugin,
    unregister_hook_plugin,
    call_hook,
    PLUGGY_AVAILABLE,
)
from strutex.plugins.discovery import PluginDiscovery


class TestLazyLoading:
    """Test lazy loading functionality."""
    
    def setup_method(self):
        PluginRegistry.clear()
    
    def test_discover_does_not_load_plugins(self):
        """Discover should store entry points without loading."""
        PluginRegistry.discover(force=True)
        
        # Check that gemini is known but not loaded
        info = PluginRegistry.get_plugin_info("provider", "gemini")
        if info:
            assert info.get("loaded") is False
    
    def test_get_loads_plugin(self):
        """Getting a plugin should load it."""
        PluginRegistry.discover(force=True)
        
        # Get the plugin (triggers load)
        cls = PluginRegistry.get("provider", "gemini")
        
        if cls:
            # Now it should be loaded
            info = PluginRegistry.get_plugin_info("provider", "gemini")
            assert info.get("loaded") is True
    
    def test_list_names_does_not_load(self):
        """list_names should not load plugins."""
        PluginRegistry.clear()
        PluginRegistry.discover(force=True)
        
        names = PluginRegistry.list_names("provider")
        
        # Should have names but none loaded yet
        info = PluginRegistry.get_plugin_info("provider", "gemini")
        if info and "gemini" in names:
            assert info.get("loaded") is False


class TestGetSorted:
    """Test the new get_sorted() method."""
    
    def setup_method(self):
        PluginRegistry.clear()
    
    def test_get_sorted_returns_list_of_tuples(self):
        """get_sorted should return list of (name, class) tuples."""
        class P1(Provider):
            priority = 30
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        class P2(Provider):
            priority = 70
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        PluginRegistry.register("provider", "low", P1)
        PluginRegistry.register("provider", "high", P2)
        
        sorted_plugins = PluginRegistry.get_sorted("provider")
        
        assert isinstance(sorted_plugins, list)
        assert all(isinstance(item, tuple) for item in sorted_plugins)
        assert all(len(item) == 2 for item in sorted_plugins)
    
    def test_get_sorted_orders_by_priority(self):
        """get_sorted should order by priority (high first by default)."""
        class LowPriority(Provider):
            priority = 20
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        class MedPriority(Provider):
            priority = 50
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        class HighPriority(Provider):
            priority = 80
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        PluginRegistry.register("provider", "low", LowPriority)
        PluginRegistry.register("provider", "med", MedPriority)
        PluginRegistry.register("provider", "high", HighPriority)
        
        sorted_plugins = PluginRegistry.get_sorted("provider")
        priorities = [cls.priority for _, cls in sorted_plugins]
        
        # Should be descending (high first)
        assert priorities == sorted(priorities, reverse=True)
    
    def test_get_sorted_reverse_false(self):
        """get_sorted with reverse=False should order low first."""
        class P1(Provider):
            priority = 80
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        class P2(Provider):
            priority = 20
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        PluginRegistry.register("provider", "high", P1)
        PluginRegistry.register("provider", "low", P2)
        
        sorted_plugins = PluginRegistry.get_sorted("provider", reverse=False)
        priorities = [cls.priority for _, cls in sorted_plugins]
        
        # Should be ascending (low first)
        assert priorities == sorted(priorities)


class TestProtocols:
    """Test Protocol types and validation."""
    
    def test_plugin_api_version_constant(self):
        """PLUGIN_API_VERSION should be defined."""
        assert PLUGIN_API_VERSION == "1.0"
    
    def test_provider_matches_protocol(self):
        """Provider subclass should match ProviderProtocol."""
        class TestProvider(Provider):
            capabilities = ["test"]
            def process(self, *args, **kwargs):
                return {}
        
        instance = TestProvider()
        assert isinstance(instance, ProviderProtocol)
    
    def test_check_plugin_version_valid(self):
        """check_plugin_version should return True for valid version."""
        class ValidPlugin(Provider):
            strutex_plugin_version = "1.0"
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        assert check_plugin_version(ValidPlugin) is True
    
    def test_check_plugin_version_invalid(self):
        """check_plugin_version should return False for invalid version."""
        class InvalidPlugin(Provider):
            strutex_plugin_version = "99.0"
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        assert check_plugin_version(InvalidPlugin) is False
    
    def test_validate_plugin_protocol_pass(self):
        """validate_plugin_protocol should return True for valid plugin."""
        class ValidProvider(Provider):
            capabilities = ["test"]
            def process(self, *args, **kwargs):
                return {}
        
        assert validate_plugin_protocol(ValidProvider, ProviderProtocol) is True


class TestPluginAttributes:
    """Test plugin version, priority, cost attributes."""
    
    def test_provider_inherits_version(self):
        """Provider subclass should inherit default version."""
        class TestProvider(Provider):
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        assert TestProvider.strutex_plugin_version == "1.0"
    
    def test_provider_inherits_priority(self):
        """Provider subclass should inherit default priority."""
        class TestProvider(Provider):
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        assert TestProvider.priority == 50
    
    def test_provider_inherits_cost(self):
        """Provider subclass should inherit default cost."""
        class TestProvider(Provider):
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        assert TestProvider.cost == 1.0
    
    def test_provider_inherits_health_check(self):
        """Provider subclass should inherit health_check."""
        class TestProvider(Provider):
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        assert TestProvider.health_check() is True
    
    def test_custom_priority_override(self):
        """Custom priority should override default."""
        class HighPriorityProvider(Provider):
            priority = 90
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        assert HighPriorityProvider.priority == 90


class TestHooks:
    """Test pluggy hook system."""
    
    @pytest.mark.skipif(not PLUGGY_AVAILABLE, reason="pluggy not installed")
    def test_get_plugin_manager_returns_manager(self):
        """get_plugin_manager should return a PluginManager."""
        pm = get_plugin_manager()
        assert pm is not None
    
    @pytest.mark.skipif(not PLUGGY_AVAILABLE, reason="pluggy not installed")
    def test_register_and_unregister_hook_plugin(self):
        """Should be able to register and unregister hook plugins."""
        class MyPlugin:
            @hookimpl
            def pre_process(self, file_path, prompt, schema, mime_type, context):
                context["called"] = True
                return None
        
        plugin = MyPlugin()
        register_hook_plugin(plugin)
        
        # Should not raise
        unregister_hook_plugin(plugin)
    
    @pytest.mark.skipif(not PLUGGY_AVAILABLE, reason="pluggy not installed")
    def test_call_hook_returns_list(self):
        """call_hook should return a list."""
        result = call_hook("pre_process",
            file_path="test.pdf",
            prompt="test",
            schema=None,
            mime_type="application/pdf",
            context={}
        )
        assert isinstance(result, list)


class TestDiscoveryCache:
    """Test discovery caching."""
    
    def test_compute_venv_hash(self):
        """Should compute a hash of installed packages."""
        cache_hash = PluginDiscovery._compute_venv_hash()
        assert isinstance(cache_hash, str)
        assert len(cache_hash) == 16  # SHA256 truncated to 16 chars
    
    def test_discover_returns_dict(self):
        """discover() should return a dict."""
        result = PluginDiscovery.discover()
        assert isinstance(result, dict)
    
    def test_get_cache_info(self):
        """get_cache_info should return dict or None."""
        # Force a discovery to create cache
        PluginDiscovery.discover(force_refresh=True)
        
        info = PluginDiscovery.get_cache_info()
        if info is not None:
            assert "cache_file" in info
            assert "is_valid" in info
    
    def test_clear_cache(self):
        """clear_cache should not raise."""
        # Should not raise even if no cache exists
        PluginDiscovery.clear_cache()


class TestPluginInfo:
    """Test get_plugin_info method."""
    
    def setup_method(self):
        PluginRegistry.clear()
    
    def test_get_plugin_info_returns_dict(self):
        """get_plugin_info should return a dict."""
        class TestProvider(Provider):
            strutex_plugin_version = "1.0"
            priority = 60
            cost = 0.5
            capabilities = ["test"]
            def process(self, *args, **kwargs): pass
        
        PluginRegistry.register("provider", "test", TestProvider)
        
        info = PluginRegistry.get_plugin_info("provider", "test")
        
        assert isinstance(info, dict)
        assert info["name"] == "test"
        assert info["version"] == "1.0"
        assert info["priority"] == 60
        assert info["cost"] == 0.5
        assert info["capabilities"] == ["test"]
        assert info["loaded"] is True
    
    def test_get_plugin_info_nonexistent(self):
        """get_plugin_info should return None for missing plugins."""
        info = PluginRegistry.get_plugin_info("provider", "nonexistent_xyz")
        assert info is None


class TestSandbox:
    """Test sandbox plugin probing."""
    
    def test_probe_plugin_metadata_returns_dict(self):
        """probe_plugin_metadata should return a dict."""
        from strutex.plugins.sandbox import probe_plugin_metadata
        
        result = probe_plugin_metadata("strutex.providers", "gemini", timeout=5.0)
        
        assert isinstance(result, dict)
        assert "name" in result
        assert "healthy" in result
    
    def test_is_plugin_safe_returns_bool(self):
        """is_plugin_safe should return a bool."""
        from strutex.plugins.sandbox import is_plugin_safe
        
        result = is_plugin_safe("strutex.providers", "gemini")
        assert isinstance(result, bool)


class TestRegisterDecorator:
    """Test @register decorator (no longer deprecated - used for aliases)."""
    
    def setup_method(self):
        PluginRegistry.clear()
    
    def test_register_does_not_emit_deprecation_warning(self):
        """@register should NOT emit DeprecationWarning (no longer deprecated)."""
        import warnings
        from strutex.plugins import register
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            @register("provider", name="alias_test")
            class AliasProvider(Provider):
                capabilities = []
                def process(self, *args, **kwargs): pass
        
        # Should have no deprecation warnings
        deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0, f"Unexpected deprecation warnings: {deprecation_warnings}"
    
    def test_register_creates_alias(self):
        """@register should create an alias alongside auto-registration."""
        from strutex.plugins import register
        
        @register("provider", name="my_alias")
        class MyProvider(Provider):
            capabilities = []
            def process(self, *args, **kwargs): pass
        
        # Should be registered under BOTH names
        assert PluginRegistry.get("provider", "myprovider") is not None
        assert PluginRegistry.get("provider", "my_alias") is not None
        assert PluginRegistry.get("provider", "myprovider") is PluginRegistry.get("provider", "my_alias")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
