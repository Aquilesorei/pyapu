"""
Tests for strutex.types module.
"""

import pytest
import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strutex.types import (
    Schema, Type, String, Number, Integer, Boolean, Array, Object
)


class TestTypeEnum:
    """Tests for the Type enum."""

    def test_type_values(self):
        """Test that all expected types exist."""
        assert Type.STRING.value == "STRING"
        assert Type.NUMBER.value == "NUMBER"
        assert Type.INTEGER.value == "INTEGER"
        assert Type.BOOLEAN.value == "BOOLEAN"
        assert Type.ARRAY.value == "ARRAY"
        assert Type.OBJECT.value == "OBJECT"


class TestSchema:
    """Tests for the base Schema class."""

    def test_schema_basic_creation(self):
        """Test basic schema creation."""
        schema = Schema(type=Type.STRING)
        assert schema.type == Type.STRING
        assert schema.description is None
        assert schema.properties is None
        assert schema.items is None
        assert schema.required == []
        assert schema.nullable is False

    def test_schema_with_all_params(self):
        """Test schema with all parameters."""
        props = {"name": Schema(type=Type.STRING)}
        schema = Schema(
            type=Type.OBJECT,
            description="A test object",
            properties=props,
            required=["name"],
            nullable=True
        )
        assert schema.type == Type.OBJECT
        assert schema.description == "A test object"
        assert schema.properties == props
        assert schema.required == ["name"]
        assert schema.nullable is True


class TestStringSchema:
    """Tests for the String helper class."""

    def test_string_default(self):
        """Test String with defaults."""
        s = String()
        assert s.type == Type.STRING
        assert s.description is None
        assert s.nullable is False

    def test_string_with_description(self):
        """Test String with description."""
        s = String(description="A name field")
        assert s.description == "A name field"

    def test_string_nullable(self):
        """Test nullable String."""
        s = String(nullable=True)
        assert s.nullable is True


class TestNumberSchema:
    """Tests for the Number helper class."""

    def test_number_default(self):
        """Test Number with defaults."""
        n = Number()
        assert n.type == Type.NUMBER
        assert n.nullable is False

    def test_number_with_description(self):
        """Test Number with description."""
        n = Number(description="Total amount")
        assert n.description == "Total amount"


class TestIntegerSchema:
    """Tests for the Integer helper class."""

    def test_integer_default(self):
        """Test Integer with defaults."""
        i = Integer()
        assert i.type == Type.INTEGER

    def test_integer_with_params(self):
        """Test Integer with parameters."""
        i = Integer(description="Count", nullable=True)
        assert i.description == "Count"
        assert i.nullable is True


class TestBooleanSchema:
    """Tests for the Boolean helper class."""

    def test_boolean_default(self):
        """Test Boolean with defaults."""
        b = Boolean()
        assert b.type == Type.BOOLEAN

    def test_boolean_with_description(self):
        """Test Boolean with description."""
        b = Boolean(description="Is active")
        assert b.description == "Is active"


class TestArraySchema:
    """Tests for the Array helper class."""

    def test_array_with_string_items(self):
        """Test Array containing Strings."""
        arr = Array(items=String())
        assert arr.type == Type.ARRAY
        assert arr.items.type == Type.STRING

    def test_array_with_object_items(self):
        """Test Array containing Objects."""
        obj = Object(properties={"name": String()})
        arr = Array(items=obj, description="List of objects")
        assert arr.type == Type.ARRAY
        assert arr.items.type == Type.OBJECT
        assert arr.description == "List of objects"


class TestObjectSchema:
    """Tests for the Object helper class."""

    def test_object_auto_required(self):
        """Test Object auto-populates required list."""
        obj = Object(properties={
            "name": String(),
            "age": Number()
        })
        assert obj.type == Type.OBJECT
        assert set(obj.required) == {"name", "age"}

    def test_object_explicit_required(self):
        """Test Object with explicit required list."""
        obj = Object(
            properties={"name": String(), "age": Number()},
            required=["name"]
        )
        assert obj.required == ["name"]

    def test_object_no_required(self):
        """Test Object with empty required list."""
        obj = Object(
            properties={"name": String()},
            required=[]
        )
        assert obj.required == []

    def test_nested_object(self):
        """Test nested Object structure."""
        inner = Object(properties={"city": String()})
        outer = Object(properties={
            "name": String(),
            "address": inner
        })
        assert outer.properties["address"].type == Type.OBJECT
        assert "city" in outer.properties["address"].properties

    def test_complex_schema(self):
        """Test complex nested schema."""
        schema = Object(
            description="Invoice data",
            properties={
                "invoice_number": String(description="The invoice ID"),
                "total": Number(),
                "items": Array(
                    items=Object(
                        properties={
                            "name": String(),
                            "price": Number(),
                            "quantity": Integer()
                        }
                    )
                )
            }
        )
        assert schema.type == Type.OBJECT
        assert schema.properties["items"].type == Type.ARRAY
        assert schema.properties["items"].items.type == Type.OBJECT
        assert "name" in schema.properties["items"].items.properties


if __name__ == "__main__":
    pytest.main([__file__, "-v"])