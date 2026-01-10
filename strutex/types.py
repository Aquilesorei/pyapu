from enum import Enum as PyEnum
from typing import List, Dict, Optional, Any, Union, Type as PyType
import json
import inspect
import builtins


class Type(PyEnum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    ARRAY = "ARRAY"
    OBJECT = "OBJECT"


class Schema:
    """
    Base class for all schema definitions.
    """

    def __init__(
            self,
            type: Type,
            description: Optional[str] = None,
            properties: Optional[Dict[str, Union['Schema', PyType['Schema']]]] = None,
            items: Optional[Union['Schema', PyType['Schema']]] = None,
            required: Optional[List[str]] = None,
            nullable: bool = False,
            enum: Optional[List[Any]] = None,
            format: Optional[str] = None,
    ):
        self.type = type
        self.description = description
        
        # Handle properties (dict of schemas)
        if properties:
            self.properties = {}
            for k, v in properties.items():
                if isinstance(v, builtins.type) and issubclass(v, Schema):
                    self.properties[k] = v()  # type: ignore
                else:
                    self.properties[k] = v
        else:
            self.properties = None  # type: ignore

        # Handle items (single schema for array)
        if items:
            if isinstance(items, builtins.type) and issubclass(items, Schema):
                self.items = items()  # type: ignore
            else:
                self.items = items
        else:
            self.items = None

            
        self.required = required or []
        self.nullable = nullable
        self.enum = enum
        self.format = format

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schema':
        # Detect type
        type_str = data.get("type")
        if not type_str:
            if "properties" in data:
                type_str = "object"
            elif "items" in data:
                type_str = "array"
            else:
                # Heuristic: If it's a non-empty dict and doesn't look like a standard schema
                # (has no standard keywords like 'type', 'description', etc.)
                # treat it as shorthand for an Object where keys are property names.
                schema_keywords = {"type", "description", "properties", "items", "required", "enum", "nullable", "format"}
                if data and not any(k in data for k in schema_keywords):
                    properties = {}
                    for k, v in data.items():
                        # If value is a string, treat as shorthand for {"type": v}
                        val_schema = {"type": v} if isinstance(v, str) else v
                        properties[k] = cls.from_dict(val_schema)
                    return Object(properties=properties)
                
                type_str = "string"
        
        # Handle list of types (e.g. ["string", "null"]) for nullable
        nullable = False
        if isinstance(type_str, list):
            if "null" in type_str:
                nullable = True
                type_str = next((t for t in type_str if t != "null"), "string")
            else:
                type_str = type_str[0]
        else:
            type_str = type_str.lower()
            
        description = data.get("description")
        
        if type_str == "string":
            return String(description=description, nullable=nullable, format=data.get("format"))
        elif type_str == "number":
            return Number(description=description, nullable=nullable)
        elif type_str == "integer":
            return Integer(description=description, nullable=nullable)
        elif type_str == "boolean":
            return Boolean(description=description, nullable=nullable)
        elif type_str == "array":
            items_data = data.get("items", {})
            # Handle item definition
            items = cls.from_dict(items_data) if items_data else String()
            return Array(items=items, description=description, nullable=nullable)
        elif type_str == "object":
            properties: Dict[str, Any] = {}
            for k, v in data.get("properties", {}).items():
                properties[k] = cls.from_dict(v)
            required = data.get("required")
            return Object(properties=properties, description=description, required=required, nullable=nullable)  # type: ignore
            
        # Default fallback
        return String(description=description, nullable=nullable)

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to JSON Schema dictionary."""
        schema: Dict[str, Any] = {
            "type": self.type.value.lower(),
        }
        
        if self.description:
            schema["description"] = self.description
            
        if self.nullable:
            # Handle nullable type (JSON Schema draft 7 style)
            schema["type"] = [schema["type"], "null"]
            
        if self.enum:
            schema["enum"] = self.enum
            
        if self.format:
            schema["format"] = self.format
            
        if self.type == Type.OBJECT:
            if self.properties:
                schema["properties"] = {
                    k: v.to_dict() for k, v in self.properties.items()
                }
            if self.required:
                schema["required"] = self.required
            schema["additionalProperties"] = False
                
        if self.type == Type.ARRAY and self.items:
            schema["items"] = self.items.to_dict()
            
        return schema

    def __repr__(self) -> str:
        parts = [f"type={self.type.value}"]
        if self.description:
            parts.append(f"desc={self.description!r}")
        if self.required:
            parts.append(f"required={self.required}")
        return f"{self.__class__.__name__}({', '.join(parts)})"
        
    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# --- Helper Classes (Syntactic Sugar) ---

class String(Schema):
    def __init__(self, description: Optional[str] = None, nullable: bool = False, format: Optional[str] = None):
        super().__init__(Type.STRING, description=description, nullable=nullable, format=format)


class Number(Schema):
    def __init__(self, description: Optional[str] = None, nullable: bool = False):
        super().__init__(Type.NUMBER, description=description, nullable=nullable)


class Integer(Schema):
    def __init__(self, description: Optional[str] = None, nullable: bool = False):
        super().__init__(Type.INTEGER, description=description, nullable=nullable)


class Boolean(Schema):
    def __init__(self, description: Optional[str] = None, nullable: bool = False):
        super().__init__(Type.BOOLEAN, description=description, nullable=nullable)


class Array(Schema):
    def __init__(self, items: Union[Schema, PyType[Schema]], description: Optional[str] = None, nullable: bool = False):
        """
        Represents a list of items.
        :param items: The Schema definition for the items inside the array.
                      Can be an instance (String()) or a class (String).
        """
        # Note: Superclass Schema handles the instantiation logic for 'items'
        super().__init__(Type.ARRAY, items=items, description=description, nullable=nullable)


class Object(Schema):
    def __init__(
            self,
            properties: Dict[str, Union[Schema, PyType[Schema]]],
            description: Optional[str] = None,
            required: Optional[List[str]] = None,
            nullable: bool = False
    ):
        """
        Represents a nested object (dictionary).

        :param properties: Dictionary mapping field names to Schema objects (or classes).
        :param required: List of keys that are mandatory.
                         If None, ALL properties are assumed required.
                         Pass [] explicitly if no fields are required.
        """
        # Superclass Schema handles instantiation logic for 'properties'
        
        # We need to pre-calculate required based on keys, before passing to super
        # But wait, super modifies properties (instantiates them).
        # However, the keys remain the same. So we can just use keys from the input dict.
        
        # Smart Default: If 'required' is missing, assume strict mode (all fields required)
        if required is None:
            calculated_required = list(properties.keys())
        else:
            calculated_required = required

        super().__init__(
            Type.OBJECT,
            properties=properties,
            description=description,
            required=calculated_required,
            nullable=nullable
        )


# --- New Specialized Types ---

class Enum(Schema):
    """
    String field restricted to a fixed set of values.
    """
    def __init__(
        self, 
        values: List[str], 
        description: Optional[str] = None, 
        nullable: bool = False
    ):
        super().__init__(
            Type.STRING, 
            description=description, 
            nullable=nullable,
            enum=values
        )


class Date(String):
    """
    String field representing a date (YYYY-MM-DD).
    """
    def __init__(self, description: Optional[str] = None, nullable: bool = False):
        desc = description or "Date in YYYY-MM-DD format"
        super().__init__(description=desc, nullable=nullable, format="date")


class DateTime(String):
    """
    String field representing a date-time (ISO 8601).
    """
    def __init__(self, description: Optional[str] = None, nullable: bool = False):
        desc = description or "DateTime in ISO 8601 format"
        super().__init__(description=desc, nullable=nullable, format="date-time")
