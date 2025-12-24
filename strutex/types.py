from enum import Enum
from typing import List, Dict, Optional, Union


class Type(Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    ARRAY = "ARRAY"
    OBJECT = "OBJECT"


class Schema:
    """
    Base class for all schema definitions.
    Users generally should use the helper classes (Object, String, etc.) instead of this directly.
    """

    def __init__(
            self,
            type: Type,
            description: Optional[str] = None,
            properties: Optional[Dict[str, 'Schema']] = None,
            items: Optional['Schema'] = None,
            required: Optional[List[str]] = None,
            nullable: bool = False
    ):
        self.type = type
        self.description = description
        self.properties = properties
        self.items = items
        self.required = required or []
        self.nullable = nullable


# --- Helper Classes (Syntactic Sugar) ---

class String(Schema):
    def __init__(self, description: str = None, nullable: bool = False):
        super().__init__(Type.STRING, description=description, nullable=nullable)


class Number(Schema):
    def __init__(self, description: str = None, nullable: bool = False):
        super().__init__(Type.NUMBER, description=description, nullable=nullable)


class Integer(Schema):
    def __init__(self, description: str = None, nullable: bool = False):
        super().__init__(Type.INTEGER, description=description, nullable=nullable)


class Boolean(Schema):
    def __init__(self, description: str = None, nullable: bool = False):
        super().__init__(Type.BOOLEAN, description=description, nullable=nullable)


class Array(Schema):
    def __init__(self, items: Schema, description: str = None, nullable: bool = False):
        """
        Represents a list of items.
        :param items: The Schema definition for the items inside the array.
        """
        super().__init__(Type.ARRAY, items=items, description=description, nullable=nullable)


class Object(Schema):
    def __init__(
            self,
            properties: Dict[str, Schema],
            description: str = None,
            required: Optional[List[str]] = None,
            nullable: bool = False
    ):
        """
        Represents a nested object (dictionary).

        :param properties: Dictionary mapping field names to Schema objects.
        :param required: List of keys that are mandatory.
                         If None, ALL properties are assumed required.
                         Pass [] explicitly if no fields are required.
        """
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