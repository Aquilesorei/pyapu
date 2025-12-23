"""
Contract tests for pyapu plugins.

These tests verify that all plugins conform to their respective protocols
and meet the requirements of the plugin system v2.

Run with: poetry run pytest tests/test_plugin_contract.py -v
"""

import pytest
from typing import Type

from pyapu.plugins import (
    PluginRegistry,
    Provider,
    Extractor,
    Validator,
    Postprocessor,
    SecurityPlugin,
    PLUGIN_API_VERSION,
)
from pyapu.plugins.protocol import (
    ProviderProtocol,
    ExtractorProtocol,
    ValidatorProtocol,
    PostprocessorProtocol,
    SecurityPluginProtocol,
    check_plugin_version,
)


class TestProviderContract:
    """Contract tests for Provider plugins."""
    
    @pytest.fixture
    def provider_class(self) -> Type[Provider]:
        """Get the built-in Gemini provider class."""
        PluginRegistry.discover()
        cls = PluginRegistry.get("provider", "gemini")
        if cls is None:
            pytest.skip("Gemini provider not found")
        return cls
    
    def test_has_plugin_version(self, provider_class: Type[Provider]):
        """All providers must declare their API version."""
        assert hasattr(provider_class, "pyapu_plugin_version")
        assert isinstance(provider_class.pyapu_plugin_version, str)
    
    def test_version_is_compatible(self, provider_class: Type[Provider]):
        """Provider version must be compatible with current API."""
        assert check_plugin_version(provider_class)
        assert provider_class.pyapu_plugin_version == PLUGIN_API_VERSION
    
    def test_has_priority(self, provider_class: Type[Provider]):
        """All providers must have a priority attribute."""
        assert hasattr(provider_class, "priority")
        assert isinstance(provider_class.priority, int)
        assert 0 <= provider_class.priority <= 100
    
    def test_has_cost(self, provider_class: Type[Provider]):
        """All providers must have a cost attribute."""
        assert hasattr(provider_class, "cost")
        assert isinstance(provider_class.cost, (int, float))
        assert provider_class.cost >= 0
    
    def test_has_capabilities(self, provider_class: Type[Provider]):
        """All providers must declare their capabilities."""
        assert hasattr(provider_class, "capabilities")
        assert isinstance(provider_class.capabilities, list)
    
    def test_has_process_method(self, provider_class: Type[Provider]):
        """All providers must implement process()."""
        assert hasattr(provider_class, "process")
        assert callable(getattr(provider_class, "process"))
    
    def test_has_health_check(self, provider_class: Type[Provider]):
        """All providers must have a health_check classmethod."""
        assert hasattr(provider_class, "health_check")
        # Should be callable on the class
        result = provider_class.health_check()
        assert isinstance(result, bool)


class TestBaseClassContracts:
    """Test that all base classes have required attributes."""
    
    def test_provider_base_class(self):
        """Provider base has all required attributes."""
        assert hasattr(Provider, "pyapu_plugin_version")
        assert hasattr(Provider, "priority")
        assert hasattr(Provider, "cost")
        assert hasattr(Provider, "capabilities")
        assert hasattr(Provider, "health_check")
    
    def test_extractor_base_class(self):
        """Extractor base has all required attributes."""
        assert hasattr(Extractor, "pyapu_plugin_version")
        assert hasattr(Extractor, "priority")
        assert hasattr(Extractor, "supported_mime_types")
        assert hasattr(Extractor, "health_check")
    
    def test_validator_base_class(self):
        """Validator base has all required attributes."""
        assert hasattr(Validator, "pyapu_plugin_version")
        assert hasattr(Validator, "priority")
        assert hasattr(Validator, "health_check")
    
    def test_postprocessor_base_class(self):
        """Postprocessor base has all required attributes."""
        assert hasattr(Postprocessor, "pyapu_plugin_version")
        assert hasattr(Postprocessor, "priority")
        assert hasattr(Postprocessor, "health_check")
    
    def test_security_plugin_base_class(self):
        """SecurityPlugin base has all required attributes."""
        assert hasattr(SecurityPlugin, "pyapu_plugin_version")
        assert hasattr(SecurityPlugin, "priority")
        assert hasattr(SecurityPlugin, "health_check")


class TestPluginRegistry:
    """Test PluginRegistry functionality."""
    
    def test_discover_returns_count(self):
        """discover() should return the number of plugins found."""
        PluginRegistry.clear()
        count = PluginRegistry.discover(force=True)
        assert isinstance(count, int)
        assert count >= 0
    
    def test_list_types_returns_list(self):
        """list_types() should return a list of strings."""
        PluginRegistry.discover()
        types = PluginRegistry.list_types()
        assert isinstance(types, list)
        # Should have at least provider type from built-ins
        assert "provider" in types or len(types) == 0
    
    def test_list_names_returns_sorted_list(self):
        """list_names() should return a sorted list of plugin names."""
        PluginRegistry.discover()
        names = PluginRegistry.list_names("provider")
        assert isinstance(names, list)
        # Should be sorted
        assert names == sorted(names)
    
    def test_get_returns_none_for_missing(self):
        """get() should return None for non-existent plugins."""
        result = PluginRegistry.get("provider", "nonexistent_plugin_xyz")
        assert result is None
    
    def test_get_plugin_info_returns_dict(self):
        """get_plugin_info() should return a dict with expected keys."""
        PluginRegistry.discover()
        info = PluginRegistry.get_plugin_info("provider", "gemini")
        
        if info is None:
            pytest.skip("Gemini provider not found")
        
        assert isinstance(info, dict)
        assert "name" in info
        assert "loaded" in info
    
    def test_clear_removes_plugins(self):
        """clear() should remove all registered plugins."""
        PluginRegistry.discover()
        PluginRegistry.clear("provider")
        
        # After clear, list should be empty
        names = PluginRegistry.list_names("provider")
        # Note: entry points will be rediscovered on next get()
        # But the cache should be empty
        assert "provider" not in PluginRegistry._loaded or len(PluginRegistry._loaded["provider"]) == 0


class TestSpecPlugin:
    """
    Test with a minimal spec-compliant plugin.
    
    This serves as a reference implementation for plugin authors.
    """
    
    def test_minimal_provider_implementation(self):
        """A minimal provider should pass all contract requirements."""
        
        class SpecProvider(Provider):
            """Minimal spec-compliant provider for testing."""
            
            pyapu_plugin_version = "1.0"
            priority = 50
            cost = 1.0
            capabilities = ["text"]
            
            def process(self, file_path, prompt, schema, mime_type, **kwargs):
                return {"_spec_test": True}
            
            @classmethod
            def health_check(cls) -> bool:
                return True
        
        # Verify it passes all checks
        assert check_plugin_version(SpecProvider)
        assert SpecProvider.pyapu_plugin_version == PLUGIN_API_VERSION
        assert 0 <= SpecProvider.priority <= 100
        assert SpecProvider.cost >= 0
        assert isinstance(SpecProvider.capabilities, list)
        assert SpecProvider.health_check() is True
        
        # Verify process works
        instance = SpecProvider()
        result = instance.process("test.pdf", "test", {}, "application/pdf")
        assert result == {"_spec_test": True}
