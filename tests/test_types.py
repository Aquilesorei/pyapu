"""
Tests for the enhanced schema system in types.py.
"""

import pytest
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex.types import (
    String, Number, Integer, Boolean, Array, Object, 
    Enum, Date, DateTime, Type
)


class TestSchemaSerialization:
    """Tests for to_dict() method."""
    
    def test_string_serialization(self):
        """Test basic string serialization."""
        s = String(description="A name")
        assert s.to_dict() == {
            "type": "string",
            "description": "A name"
        }
        
    def test_nullable_serialization(self):
        """Test nullable field serialization."""
        s = String(nullable=True)
        assert s.to_dict() == {
            # JSON schema draft 7 style for nullable
            "type": ["string", "null"] 
        }
        
    def test_object_serialization(self):
        """Test recursive object serialization."""
        schema = Object(
            properties={
                "name": String(description="Name"),
                "age": Integer(description="Age")
            },
            required=["name"]
        )
        
        expected = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name"},
                "age": {"type": "integer", "description": "Age"}
            },
            "required": ["name"],
            "additionalProperties": False
        }
        
        assert schema.to_dict() == expected
        
    def test_object_default_required(self):
        """Test strict mode (all required by default)."""
        schema = Object(
            properties={
                "a": String(), 
                "b": Number()
            }
        )
        assert set(schema.to_dict()["required"]) == {"a", "b"}

    def test_array_serialization(self):
        """Test array serialization."""
        schema = Array(
            items=String(),
            description="List of tags"
        )
        
        expected = {
            "type": "array",
            "description": "List of tags",
            "items": {"type": "string"}
        }
        
        assert schema.to_dict() == expected


class TestSpecializedTypes:
    """Tests for new Enum, Date, DateTime types."""
    
    def test_enum_serialization(self):
        """Test Enum serialization."""
        schema = Enum(
            values=["A", "B", "C"],
            description="Category"
        )
        
        expected = {
            "type": "string",
            "description": "Category",
            "enum": ["A", "B", "C"]
        }
        
        assert schema.to_dict() == expected
        
    def test_date_serialization(self):
        """Test Date serialization."""
        schema = Date(description="Birthday")
        
        expected = {
            "type": "string",
            "description": "Birthday",
            "format": "date"
        }
        
        assert schema.to_dict() == expected
        
    def test_datetime_serialization(self):
        """Test DateTime serialization."""
        schema = DateTime(description="Created at")
        
        expected = {
            "type": "string",
            "description": "Created at",
            "format": "date-time"
        }
        
        assert schema.to_dict() == expected


class TestSyntacticSugar:
    """Tests for using classes instead of instances (e.g. String vs String())."""
    
    def test_object_with_classes(self):
        """Test defining Object properties with classes."""
        schema = Object(
            properties={
                "name": String,  # Class, not instance
                "age": Integer   # Class, not instance
            }
        )
        
        d = schema.to_dict()
        assert d["properties"]["name"]["type"] == "string"
        assert d["properties"]["age"]["type"] == "integer"
        
    def test_array_with_class(self):
        """Test defining Array items with class."""
        schema = Array(items=String)  # Class, not instance
        
        d = schema.to_dict()
        assert d["items"]["type"] == "string"

    def test_mixed_usage(self):
        """Test mixing classes and instances."""
        schema = Object(
            properties={
                "simple": String,
                "complex": String(description="Detailed")
            }
        )
        
        d = schema.to_dict()
        assert d["properties"]["simple"]["type"] == "string"
        assert "description" not in d["properties"]["simple"]
        
        assert d["properties"]["complex"]["type"] == "string"
        assert d["properties"]["complex"]["description"] == "Detailed"


class TestSchemaStringRep:
    """Tests for __str__ and __repr__."""
    
    def test_repr(self):
        """Test readable representation."""
        s = String(description="test")
        assert "String(type=STRING, desc='test')" in repr(s)
        
    def test_str_json(self):
        """Test string conversion dumps JSON."""
        s = String(description="test")
        json_str = str(s)
        parsed = json.loads(json_str)
        assert parsed["type"] == "string"
        assert parsed["description"] == "test"


class TestSchemaSyntacticSugar:
    """Tests for passing classes instead of instances."""
    
    def test_object_with_classes(self):
        """Test properties taking classes."""
        schema = Object(
            properties={
                "name": String,  # Passing class without parens
                "age": Integer,
                "active": Boolean
            }
        )
        
        d = schema.to_dict()
        props = d["properties"]
        assert props["name"]["type"] == "string"
        assert props["age"]["type"] == "integer"
        assert props["active"]["type"] == "boolean"

    def test_array_with_class(self):
        """Test items taking class."""
        schema = Array(
            items=String,  # Passing class
            description="Tags"
        )
        
        d = schema.to_dict()
        assert d["items"]["type"] == "string"
        
    def test_mixed_usage(self):
        """Test mixing classes and instances."""
        schema = Object(
            properties={
                "name": String(description="Name"),  # Instance
                "id": Integer,                       # Class
                "tags": Array(items=String)          # Class inside Array
            }
        )
        
        d = schema.to_dict()
        assert d["properties"]["name"]["description"] == "Name"
        assert d["properties"]["id"]["type"] == "integer"
        assert d["properties"]["tags"]["items"]["type"] == "string"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])