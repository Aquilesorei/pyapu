"""
Pydantic model support for strutex schemas.

Converts Pydantic BaseModel classes to strutex Schema objects
and validates extraction results against Pydantic models.
"""

from typing import Any, Dict, Type, Union, get_type_hints, get_origin, get_args
import inspect

from .types import Schema, Type as StrutexType, String, Number, Integer, Boolean, Array, Object


def pydantic_to_schema(model: Type) -> Schema:
    """
    Convert a Pydantic BaseModel to a strutex Schema.
    
    Args:
        model: A Pydantic BaseModel class
        
    Returns:
        Equivalent strutex Schema (Object)
        
    Example:
        from pydantic import BaseModel
        
        class Invoice(BaseModel):
            invoice_number: str
            total: float
            items: list[LineItem]
        
        schema = pydantic_to_schema(Invoice)
    """
    try:
        from pydantic import BaseModel
        from pydantic.fields import FieldInfo
    except ImportError:
        raise ImportError("Pydantic is required for pydantic_to_schema. Install with: pip install pydantic")
    
    if not (inspect.isclass(model) and issubclass(model, BaseModel)):
        raise TypeError(f"Expected Pydantic BaseModel, got {type(model)}")
    
    properties = {}
    required_fields = []
    
    # Get model fields
    for field_name, field_info in model.model_fields.items():
        field_type = field_info.annotation
        description = field_info.description
        
        # Check if required
        if field_info.is_required():
            required_fields.append(field_name)
        
        # Convert type to schema
        properties[field_name] = _python_type_to_schema(
            field_type, 
            description=description,
            nullable=not field_info.is_required()
        )
    
    return Object(
        properties=properties,
        description=model.__doc__,
        required=required_fields if required_fields else None
    )


def _python_type_to_schema(
    python_type: Any,
    description: str = None,
    nullable: bool = False
) -> Schema:
    """Convert a Python type annotation to a strutex Schema."""
    try:
        from pydantic import BaseModel
    except ImportError:
        BaseModel = None
    
    # Handle None type
    if python_type is type(None):
        return String(nullable=True)
    
    # Handle basic types
    if python_type is str:
        return String(description=description, nullable=nullable)
    elif python_type in (int,):
        return Integer(description=description, nullable=nullable)
    elif python_type in (float,):
        return Number(description=description, nullable=nullable)
    elif python_type is bool:
        return Boolean(description=description, nullable=nullable)
    
    # Handle generic types (List, Dict, Optional, etc.)
    origin = get_origin(python_type)
    args = get_args(python_type)
    
    # Handle Optional[X] (Union[X, None])
    if origin is Union:
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return _python_type_to_schema(non_none_args[0], description, nullable=True)
        # For complex unions, default to string
        return String(description=description, nullable=True)
    
    # Handle List[X]
    if origin is list:
        item_type = args[0] if args else str
        return Array(
            items=_python_type_to_schema(item_type),
            description=description,
            nullable=nullable
        )
    
    # Handle Dict (treat as object)
    if origin is dict:
        return Object(
            properties={},
            description=description,
            required=[],
            nullable=nullable
        )
    
    # Handle nested Pydantic models
    if BaseModel and inspect.isclass(python_type) and issubclass(python_type, BaseModel):
        nested = pydantic_to_schema(python_type)
        # Copy nullable setting
        nested.nullable = nullable
        if description and not nested.description:
            nested.description = description
        return nested
    
    # Default to string
    return String(description=description, nullable=nullable)


def validate_with_pydantic(data: Dict[str, Any], model: Type) -> Any:
    """
    Validate extracted data against a Pydantic model.
    
    Args:
        data: Extracted dictionary data
        model: Pydantic BaseModel class to validate against
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        pydantic.ValidationError: If validation fails
    """
    try:
        from pydantic import BaseModel
    except ImportError:
        raise ImportError("Pydantic is required. Install with: pip install pydantic")
    
    if not (inspect.isclass(model) and issubclass(model, BaseModel)):
        raise TypeError(f"Expected Pydantic BaseModel, got {type(model)}")
    
    return model.model_validate(data)
