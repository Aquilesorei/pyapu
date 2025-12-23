"""
Tests for pyapu.plugins module.
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyapu.plugins.registry import PluginRegistry, register
from pyapu.plugins.base import Provider, Extractor, Validator, Postprocessor, SecurityPlugin


class TestPluginRegistry:
    """Tests for PluginRegistry class."""
    
    def setup_method(self):
        """Clear registry before each test."""
        PluginRegistry.clear()
    
    def test_register_and_get(self):
        """Test basic register and get."""
        class MyProvider:
            pass
        
        PluginRegistry.register("provider", "test", MyProvider)
        assert PluginRegistry.get("provider", "test") == MyProvider
    
    def test_get_nonexistent(self):
        """Test get returns None for missing plugins."""
        assert PluginRegistry.get("provider", "nonexistent") is None
    
    def test_case_insensitive(self):
        """Test names are case-insensitive."""
        class MyProvider:
            pass
        
        PluginRegistry.register("provider", "TestProvider", MyProvider)
        assert PluginRegistry.get("provider", "testprovider") == MyProvider
        assert PluginRegistry.get("provider", "TESTPROVIDER") == MyProvider
    
    def test_list_plugins(self):
        """Test listing all plugins of a type."""
        class P1:
            pass
        class P2:
            pass
        
        PluginRegistry.register("test_type", "p1", P1)
        PluginRegistry.register("test_type", "p2", P2)
        
        plugins = PluginRegistry.list("test_type")
        assert len(plugins) == 2
        assert plugins["p1"] == P1
        assert plugins["p2"] == P2
    
    def test_list_types(self):
        """Test listing all plugin types."""
        class P:
            pass
        
        PluginRegistry.register("provider", "p", P)
        PluginRegistry.register("validator", "v", P)
        
        types = PluginRegistry.list_types()
        assert "provider" in types
        assert "validator" in types
    
    def test_clear_specific_type(self):
        """Test clearing a specific plugin type."""
        class P:
            pass
        
        PluginRegistry.register("provider", "p", P)
        PluginRegistry.register("validator", "v", P)
        
        PluginRegistry.clear("provider")
        
        assert PluginRegistry.get("provider", "p") is None
        assert PluginRegistry.get("validator", "v") == P
    
    def test_clear_all(self):
        """Test clearing all manually registered plugins."""
        class P:
            pass
        
        PluginRegistry.register("test_provider", "p", P)
        PluginRegistry.register("test_validator", "v", P)
        
        PluginRegistry.clear()
        
        # After clear, manual registrations are gone
        # Note: list_types may still return entry point types on re-discovery
        assert PluginRegistry.get("test_provider", "p") is None
        assert PluginRegistry.get("test_validator", "v") is None


class TestRegisterDecorator:
    """Tests for @register decorator."""
    
    def setup_method(self):
        """Clear registry before each test."""
        PluginRegistry.clear()
    
    def test_register_with_explicit_name(self):
        """Test decorator with explicit name."""
        @register("provider", name="custom_name")
        class MyProvider:
            pass
        
        assert PluginRegistry.get("provider", "custom_name") == MyProvider
    
    def test_register_auto_name(self):
        """Test decorator auto-names from class name."""
        @register("provider")
        class AutoNamedProvider:
            pass
        
        assert PluginRegistry.get("provider", "autonamedprovider") == AutoNamedProvider
    
    def test_decorator_returns_class(self):
        """Test decorator returns the original class."""
        @register("provider")
        class TestClass:
            pass
        
        assert TestClass.__name__ == "TestClass"


class TestBaseClasses:
    """Tests for abstract base classes."""
    
    def test_provider_is_abstract(self):
        """Test Provider can't be instantiated."""
        with pytest.raises(TypeError):
            Provider()
    
    def test_extractor_is_abstract(self):
        """Test Extractor can't be instantiated."""
        with pytest.raises(TypeError):
            Extractor()
    
    def test_validator_is_abstract(self):
        """Test Validator can't be instantiated."""
        with pytest.raises(TypeError):
            Validator()
    
    def test_postprocessor_is_abstract(self):
        """Test Postprocessor can't be instantiated."""
        with pytest.raises(TypeError):
            Postprocessor()
    
    def test_security_plugin_default_methods(self):
        """Test SecurityPlugin has working default methods."""
        # SecurityPlugin is not fully abstract, has defaults
        class MySecurityPlugin(SecurityPlugin):
            pass
        
        plugin = MySecurityPlugin()
        
        input_result = plugin.validate_input("test")
        assert input_result.valid is True
        assert input_result.text == "test"
        
        output_result = plugin.validate_output({"key": "value"})
        assert output_result.valid is True


class TestConcreteProvider:
    """Test implementing a concrete Provider."""
    
    def test_concrete_provider(self):
        """Test creating a concrete provider implementation."""
        from pyapu.types import Schema, Type
        
        class TestProvider(Provider):
            capabilities = ["test"]
            
            def process(self, file_path, prompt, schema, mime_type, **kwargs):
                return {"extracted": True}
        
        provider = TestProvider()
        assert provider.has_capability("test")
        assert not provider.has_capability("vision")
        
        result = provider.process("test.pdf", "prompt", Schema(Type.OBJECT), "application/pdf")
        assert result == {"extracted": True}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
