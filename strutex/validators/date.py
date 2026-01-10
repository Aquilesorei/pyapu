"""
Date validator - validates date formats and ranges.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..plugins.base import Validator, ValidationResult


class DateValidator(Validator, name="date"):
    """
    Validates date fields for format and range.
    
    Checks:
    - Date strings match expected formats
    - Dates are within acceptable range
    - Optional normalization to ISO format
    
    Attributes:
        date_fields: List of field names to validate
        formats: Accepted date formats (strptime patterns)
        min_date: Minimum acceptable date
        max_date: Maximum acceptable date
    """
    
    priority = 50
    
    # Common date formats
    DEFAULT_FORMATS = [
        "%Y-%m-%d",      # ISO: 2024-01-15
        "%d.%m.%Y",      # European: 15.01.2024
        "%d/%m/%Y",      # European slash: 15/01/2024
        "%m/%d/%Y",      # US: 01/15/2024
        "%d-%m-%Y",      # European dash: 15-01-2024
        "%Y/%m/%d",      # Alt ISO: 2024/01/15
    ]
    
    def __init__(
        self,
        date_fields: Optional[List[str]] = None,
        formats: Optional[List[str]] = None,
        min_year: int = 1900,
        max_year: int = 2100,
    ):
        """
        Initialize the date validator.
        
        Args:
            date_fields: Field names to validate (None = auto-detect)
            formats: Accepted date formats
            min_year: Minimum acceptable year
            max_year: Maximum acceptable year
        """
        self.date_fields = date_fields
        self.formats = formats or self.DEFAULT_FORMATS
        self.min_year = min_year
        self.max_year = max_year
    
    def validate(
        self,
        data: Dict[str, Any],
        schema: Any = None,
        source_text: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate date fields in the data.
        
        Args:
            data: The extracted data to validate
            schema: Not used by this validator
            
        Returns:
            ValidationResult with validation status
        """
        issues = []
        
        # Determine which fields to check
        if self.date_fields:
            fields_to_check = self.date_fields
        else:
            # Auto-detect: look for fields with "date" in the name
            fields_to_check = [
                k for k in data.keys() 
                if "date" in k.lower()
            ]
        
        for field in fields_to_check:
            value = data.get(field)
            if value is None or value == "":
                continue
            
            if not isinstance(value, str):
                continue
            
            # Try to parse the date
            parsed_date = None
            for fmt in self.formats:
                try:
                    parsed_date = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                issues.append(f"{field}: invalid date format '{value}'")
                continue
            
            # Check year range
            if parsed_date.year < self.min_year:
                issues.append(f"{field}: year {parsed_date.year} is before {self.min_year}")
            elif parsed_date.year > self.max_year:
                issues.append(f"{field}: year {parsed_date.year} is after {self.max_year}")
        
        return ValidationResult(
            valid=len(issues) == 0,
            data=data,
            issues=issues
        )
