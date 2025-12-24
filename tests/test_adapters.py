"""
Tests for strutex.adapters module.
"""
import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from strutex.types import Schema, Type, String, Number, Integer, Boolean, Array, Object
from strutex.adapters import SchemaAdapter

class TestSchemaAdapterOpenAI:
    """Tests for OpenAI schema conversion."""

    def test_string_conversion(self):
        """Test String to OpenAI schema."""
        schema = String(description="A name")
        result = SchemaAdapter.to_openai(schema)
        
        assert result["type"] == "string"
        assert result["description"] == "A name"

    def test_number_conversion(self):
        """Test Number to OpenAI schema."""
        schema = Number(description="Amount")
        result = SchemaAdapter.to_openai(schema)
        
        assert result["type"] == "number"
        assert result["description"] == "Amount"

    def test_integer_conversion(self):
        """Test Integer to OpenAI schema."""
        schema = Integer()
        result = SchemaAdapter.to_openai(schema)
        
        assert result["type"] == "integer"

    def test_boolean_conversion(self):
        """Test Boolean to OpenAI schema."""
        schema = Boolean()
        result = SchemaAdapter.to_openai(schema)
        
        assert result["type"] == "boolean"

    def test_array_conversion(self):
        """Test Array to OpenAI schema."""
        schema = Array(items=String())
        result = SchemaAdapter.to_openai(schema)
        
        assert result["type"] == "array"
        assert result["items"]["type"] == "string"

    def test_object_conversion(self):
        """Test Object to OpenAI schema."""
        schema = Object(properties={
            "name": String(),
            "age": Number()
        })
        result = SchemaAdapter.to_openai(schema)
        
        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["name"]["type"] == "string"
        assert result["properties"]["age"]["type"] == "number"
        assert result["additionalProperties"] is False

    def test_object_required_fields(self):
        """Test Object required fields are included."""
        schema = Object(
            properties={"name": String(), "age": Number()},
            required=["name"]
        )
        result = SchemaAdapter.to_openai(schema)
        
        assert result["required"] == ["name"]

    def test_nested_object_conversion(self):
        """Test nested Object conversion."""
        schema = Object(properties={
            "person": Object(properties={
                "name": String(),
                "address": Object(properties={
                    "city": String()
                })
            })
        })
        result = SchemaAdapter.to_openai(schema)
        
        assert result["type"] == "object"
        person = result["properties"]["person"]
        assert person["type"] == "object"
        address = person["properties"]["address"]
        assert address["type"] == "object"
        assert address["properties"]["city"]["type"] == "string"

    def test_complex_schema_conversion(self):
        """Test complex nested schema with arrays and objects."""
        schema = Object(
            description="Invoice",
            properties={
                "invoice_number": String(description="Invoice ID"),
                "total": Number(),
                "items": Array(
                    items=Object(
                        properties={
                            "name": String(),
                            "price": Number(),
                            "qty": Integer()
                        }
                    )
                )
            }
        )
        result = SchemaAdapter.to_openai(schema)
        
        assert result["type"] == "object"
        assert result["description"] == "Invoice"
        
        items = result["properties"]["items"]
        assert items["type"] == "array"
        
        item_schema = items["items"]
        assert item_schema["type"] == "object"
        assert item_schema["properties"]["name"]["type"] == "string"
        assert item_schema["properties"]["qty"]["type"] == "integer"


class TestSchemaAdapterGoogle:
    """Tests for Google schema conversion.
    
    Note: These tests require google-genai to be installed.
    They are skipped if the package is not available.
    """

    @pytest.fixture
    def google_types(self):
        """Get google.genai.types if available."""
        try:
            from google.genai import types as g_types
            return g_types
        except ImportError:
            pytest.skip("google-genai not installed")

    def test_string_conversion(self, google_types):
        """Test String to Google schema."""
        schema = String(description="A name")
        result = SchemaAdapter.to_google(schema)
        
        assert result.type == google_types.Type.STRING
        assert result.description == "A name"

    def test_number_conversion(self, google_types):
        """Test Number to Google schema."""
        schema = Number()
        result = SchemaAdapter.to_google(schema)
        
        assert result.type == google_types.Type.NUMBER

    def test_object_conversion(self, google_types):
        """Test Object to Google schema."""
        schema = Object(properties={
            "name": String(),
            "value": Number()
        })
        result = SchemaAdapter.to_google(schema)
        
        assert result.type == google_types.Type.OBJECT
        assert "name" in result.properties
        assert "value" in result.properties

    def test_array_conversion(self, google_types):
        """Test Array to Google schema."""
        schema = Array(items=String())
        result = SchemaAdapter.to_google(schema)
        
        assert result.type == google_types.Type.ARRAY
        assert result.items.type == google_types.Type.STRING

    def test_nullable_preserved(self, google_types):
        """Test nullable flag is preserved."""
        schema = String(nullable=True)
        result = SchemaAdapter.to_google(schema)
        
        assert result.nullable is True

    def test_required_preserved(self, google_types):
        """Test required list is preserved."""
        schema = Object(
            properties={"name": String()},
            required=["name"]
        )
        result = SchemaAdapter.to_google(schema)
        
        assert result.required == ["name"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])