"""
Tests for strutex.pydantic_support module.
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Skip all tests if pydantic is not installed
pydantic = pytest.importorskip("pydantic")
from pydantic import BaseModel, Field
from typing import List, Optional

from strutex.pydantic_support import pydantic_to_schema, validate_with_pydantic
from strutex.types import Type


class TestPydanticToSchema:
    """Tests for pydantic_to_schema conversion."""
    
    def test_simple_model(self):
        """Test simple model conversion."""
        class SimpleModel(BaseModel):
            name: str
            age: int
        
        schema = pydantic_to_schema(SimpleModel)
        
        assert schema.type == Type.OBJECT
        assert "name" in schema.properties
        assert "age" in schema.properties
        assert schema.properties["name"].type == Type.STRING
        assert schema.properties["age"].type == Type.INTEGER
    
    def test_with_descriptions(self):
        """Test field descriptions are preserved."""
        class DescribedModel(BaseModel):
            name: str = Field(description="The person's name")
        
        schema = pydantic_to_schema(DescribedModel)
        assert schema.properties["name"].description == "The person's name"
    
    def test_optional_fields(self):
        """Test optional fields are handled."""
        class OptionalModel(BaseModel):
            required_field: str
            optional_field: Optional[str] = None
        
        schema = pydantic_to_schema(OptionalModel)
        assert "required_field" in schema.required
        # Optional field should be nullable
        assert schema.properties["optional_field"].nullable is True
    
    def test_list_field(self):
        """Test list fields are converted to Array."""
        class ListModel(BaseModel):
            items: List[str]
        
        schema = pydantic_to_schema(ListModel)
        assert schema.properties["items"].type == Type.ARRAY
        assert schema.properties["items"].items.type == Type.STRING
    
    def test_nested_model(self):
        """Test nested Pydantic models."""
        class Address(BaseModel):
            street: str
            city: str
        
        class Person(BaseModel):
            name: str
            address: Address
        
        schema = pydantic_to_schema(Person)
        
        assert schema.properties["address"].type == Type.OBJECT
        assert "street" in schema.properties["address"].properties
        assert "city" in schema.properties["address"].properties
    
    def test_complex_nested_model(self):
        """Test complex nested model with lists."""
        class LineItem(BaseModel):
            description: str
            amount: float
        
        class Invoice(BaseModel):
            number: str
            total: float
            items: List[LineItem]
        
        schema = pydantic_to_schema(Invoice)
        
        # Check items is an array
        items_schema = schema.properties["items"]
        assert items_schema.type == Type.ARRAY
        
        # Check items contain objects with correct properties
        item_schema = items_schema.items
        assert item_schema.type == Type.OBJECT
        assert "description" in item_schema.properties
        assert "amount" in item_schema.properties
    
    def test_float_becomes_number(self):
        """Test float fields become Number."""
        class FloatModel(BaseModel):
            value: float
        
        schema = pydantic_to_schema(FloatModel)
        assert schema.properties["value"].type == Type.NUMBER
    
    def test_bool_field(self):
        """Test boolean fields."""
        class BoolModel(BaseModel):
            is_active: bool
        
        schema = pydantic_to_schema(BoolModel)
        assert schema.properties["is_active"].type == Type.BOOLEAN
    
    def test_invalid_input(self):
        """Test error on non-model input."""
        with pytest.raises(TypeError):
            pydantic_to_schema(str)
        
        with pytest.raises(TypeError):
            pydantic_to_schema("not a model")


class TestValidateWithPydantic:
    """Tests for validate_with_pydantic function."""
    
    def test_valid_data(self):
        """Test validation of correct data."""
        class SimpleModel(BaseModel):
            name: str
            value: int
        
        data = {"name": "test", "value": 42}
        result = validate_with_pydantic(data, SimpleModel)
        
        assert isinstance(result, SimpleModel)
        assert result.name == "test"
        assert result.value == 42
    
    def test_invalid_data_raises(self):
        """Test validation error on invalid data."""
        class SimpleModel(BaseModel):
            name: str
            value: int
        
        data = {"name": "test", "value": "not an int"}
        
        with pytest.raises(Exception):  # pydantic.ValidationError
            validate_with_pydantic(data, SimpleModel)
    
    def test_nested_validation(self):
        """Test validation of nested structures."""
        class Inner(BaseModel):
            field: str
        
        class Outer(BaseModel):
            inner: Inner
        
        data = {"inner": {"field": "value"}}
        result = validate_with_pydantic(data, Outer)
        
        assert isinstance(result, Outer)
        assert isinstance(result.inner, Inner)
        assert result.inner.field == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
