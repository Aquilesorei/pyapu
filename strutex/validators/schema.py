"""
Schema validator - validates output structure matches expected schema.
"""

from typing import Any, Dict, List, Optional

from ..plugins.base import Validator, ValidationResult
from ..types import Schema, Object, Array, String, Number, Boolean


class SchemaValidator(Validator, name="schema"):
    """
    Validates that extracted data matches the expected schema structure.
    
    Checks:
    - Required fields are present
    - Field types match (string, number, boolean, array, object)
    - Nested objects are validated recursively
    
    Attributes:
        strict: If True, fail on extra fields not in schema
    """
    
    priority = 80  # Run early in validation chain
    
    def __init__(self, strict: bool = False):
        """
        Initialize the schema validator.
        
        Args:
            strict: If True, reject data with fields not in schema
        """
        self.strict = strict
    
    def validate(
        self,
        data: Dict[str, Any],
        schema: Optional[Schema] = None,
        source_text: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate data against a schema.
        
        Args:
            data: The extracted data to validate
            schema: The expected schema structure
            
        Returns:
            ValidationResult with validation status and any issues
        """
        if schema is None:
            return ValidationResult(valid=True, data=data)
        
        issues: List[str] = []
        self._validate_value(data, schema, "", issues)
        
        return ValidationResult(
            valid=len(issues) == 0,
            data=data,
            issues=issues
        )
    
    def _validate_value(
        self, 
        value: Any, 
        schema: Schema, 
        path: str, 
        issues: List[str]
    ) -> None:
        """Recursively validate a value against its schema."""
        
        if isinstance(schema, Object):
            if not isinstance(value, dict):
                issues.append(f"{path or 'root'}: expected object, got {type(value).__name__}")
                return
            
            # Check required properties
            for prop_name, prop_schema in (schema.properties or {}).items():
                prop_path = f"{path}.{prop_name}" if path else prop_name
                
                if prop_name not in value:
                    if getattr(prop_schema, 'required', True):
                        issues.append(f"{prop_path}: required field missing")
                else:
                    self._validate_value(value[prop_name], prop_schema, prop_path, issues)
            
            # Check for extra fields in strict mode
            if self.strict and schema.properties:
                for key in value.keys():
                    if key not in schema.properties:
                        issues.append(f"{path}.{key}: unexpected field")
        
        elif isinstance(schema, Array):
            if not isinstance(value, list):
                issues.append(f"{path or 'root'}: expected array, got {type(value).__name__}")
                return
            
            if schema.items:
                for i, item in enumerate(value):
                    item_path = f"{path}[{i}]"
                    self._validate_value(item, schema.items, item_path, issues)
        
        elif isinstance(schema, String):
            if not isinstance(value, str):
                issues.append(f"{path or 'root'}: expected string, got {type(value).__name__}")
        
        elif isinstance(schema, Number):
            if not isinstance(value, (int, float)):
                issues.append(f"{path or 'root'}: expected number, got {type(value).__name__}")
        
        elif isinstance(schema, Boolean):
            if not isinstance(value, bool):
                issues.append(f"{path or 'root'}: expected boolean, got {type(value).__name__}")
