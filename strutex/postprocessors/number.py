"""
Number postprocessor - parses formatted numbers to float.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set

from ..plugins.base import Postprocessor


class NumberPostprocessor(Postprocessor, name="number"):
    """
    Parse formatted number strings to float values.
    
    Handles currency symbols, thousand separators, and different
    decimal formats (US vs European).
    
    Attributes:
        number_fields: Specific fields to process (None = auto-detect)
        locale: Locale hint for number format ("en_US" or "de_DE")
        
    Example:
        >>> post = NumberPostprocessor()
        >>> post.process({"total": "$1,234.56"})
        {"total": 1234.56}
        
        >>> post = NumberPostprocessor(locale="de_DE")
        >>> post.process({"total": "1.234,56 €"})
        {"total": 1234.56}
    """
    
    priority = 55
    
    # Currency symbols to strip
    CURRENCY_SYMBOLS = {"$", "€", "£", "¥", "₹", "₽", "₿", "CHF", "USD", "EUR", "GBP"}
    
    # Field name patterns that suggest numeric content
    NUMERIC_PATTERNS = {"amount", "total", "subtotal", "price", "cost", "fee", "tax", "sum", "qty", "quantity"}
    
    def __init__(
        self,
        number_fields: Optional[List[str]] = None,
        locale: str = "en_US"
    ):
        """
        Initialize the number postprocessor.
        
        Args:
            number_fields: Specific field names to process. If None, auto-detects
                fields with numeric-sounding names.
            locale: Locale hint for parsing. "en_US" uses comma as thousand sep,
                "de_DE" uses period as thousand sep.
        """
        self.number_fields = number_fields
        self.locale = locale
        
        # Determine separators based on locale
        if locale.startswith("de") or locale.startswith("fr") or locale.startswith("es"):
            self.thousand_sep = "."
            self.decimal_sep = ","
        else:
            self.thousand_sep = ","
            self.decimal_sep = "."
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse number fields in the data.
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            Data with parsed number fields
        """
        result = data.copy()
        
        fields_to_process = self._get_fields_to_process(data)
        
        for field in fields_to_process:
            value = data.get(field)
            if value is None or value == "":
                continue
            
            # Skip if already a number
            if isinstance(value, (int, float)):
                continue
                
            parsed = self._parse_number(value)
            if parsed is not None:
                result[field] = parsed
        
        return result
    
    def _get_fields_to_process(self, data: Dict[str, Any]) -> List[str]:
        """Determine which fields to process."""
        if self.number_fields:
            return [f for f in self.number_fields if f in data]
        
        # Auto-detect: fields with numeric-sounding names
        fields = []
        for key in data.keys():
            key_lower = key.lower()
            for pattern in self.NUMERIC_PATTERNS:
                if pattern in key_lower:
                    fields.append(key)
                    break
        return fields
    
    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse a formatted number string to float."""
        if not isinstance(value, str):
            return None
        
        text = value.strip()
        if not text:
            return None
        
        # Remove currency symbols and whitespace
        for symbol in self.CURRENCY_SYMBOLS:
            text = text.replace(symbol, "")
        text = text.strip()
        
        # Handle parentheses for negative numbers: (123.45) -> -123.45
        if text.startswith("(") and text.endswith(")"):
            text = "-" + text[1:-1]
        
        # Handle minus sign variations
        text = text.replace("−", "-").replace("–", "-")
        
        # Normalize to standard format
        # Remove thousand separators, convert decimal separator to period
        text = text.replace(self.thousand_sep, "")
        text = text.replace(self.decimal_sep, ".")
        
        # Remove any remaining non-numeric chars except . and -
        text = re.sub(r"[^\d.\-]", "", text)
        
        if not text or text == "-":
            return None
        
        try:
            # Use Decimal for precision, then convert to float
            return float(Decimal(text))
        except (InvalidOperation, ValueError):
            return None
