"""
Date postprocessor - normalizes date fields to ISO format.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..plugins.base import Postprocessor


def _generate_date_formats(
    separators: List[str],
    include_long_months: bool = True
) -> List[str]:
    """
    Dynamically generate all date format combinations.
    
    Args:
        separators: List of separator characters (e.g., ["-", "/", "."])
        include_long_months: Include text month formats (January, Jan)
        
    Returns:
        List of strptime format patterns
    """
    formats = []
    
    # Numeric patterns: combinations of day, month, year with separators
    # %d = day (01-31), %m = month (01-12), %Y = 4-digit year, %y = 2-digit year
    numeric_patterns = [
        ("%Y", "%m", "%d"),   # ISO: 2024-01-15
        ("%d", "%m", "%Y"),   # European: 15-01-2024
        ("%m", "%d", "%Y"),   # US: 01-15-2024
        ("%d", "%m", "%y"),   # European short: 15-01-24
        ("%m", "%d", "%y"),   # US short: 01-15-24
        ("%y", "%m", "%d"),   # Short ISO: 24-01-15
    ]
    
    for sep in separators:
        for p1, p2, p3 in numeric_patterns:
            formats.append(f"{p1}{sep}{p2}{sep}{p3}")
    
    # No-separator formats
    formats.extend([
        "%Y%m%d",   # 20240115
        "%d%m%Y",   # 15012024
        "%m%d%Y",   # 01152024
    ])
    
    if include_long_months:
        # Text month formats 
        text_patterns = [
            "%B %d, %Y",      # January 15, 2024
            "%b %d, %Y",      # Jan 15, 2024
            "%d %B %Y",       # 15 January 2024
            "%d %b %Y",       # 15 Jan 2024
            "%B %d %Y",       # January 15 2024
            "%b %d %Y",       # Jan 15 2024
            "%d. %B %Y",      # 15. January 2024 (German)
            "%d. %b %Y",      # 15. Jan 2024
            "%d-%b-%Y",       # 15-Jan-2024
            "%d-%B-%Y",       # 15-January-2024
            "%Y-%b-%d",       # 2024-Jan-15
            "%B %Y",          # January 2024 (month-year only)
            "%b %Y",          # Jan 2024
        ]
        formats.extend(text_patterns)
    
    return formats


class DatePostprocessor(Postprocessor, name="date"):
    """
    Normalize date fields to ISO format (YYYY-MM-DD).
    
    Dynamically generates all possible date format combinations from
    a list of separators and pattern components.
    
    Attributes:
        date_fields: Specific fields to process (None = auto-detect)
        separators: List of separator characters for date components
        output_format: Output strftime pattern
        min_year: Minimum acceptable year (validation)
        max_year: Maximum acceptable year (validation)
        
    Example:
        >>> post = DatePostprocessor()
        >>> post.process({"invoice_date": "15.01.2024"})
        {"invoice_date": "2024-01-15"}
        
        >>> post = DatePostprocessor(separators=["-", "/", ".", " "])
        >>> post.process({"date": "15 01 2024"})
        {"date": "2024-01-15"}
    """
    
    priority = 60
    
    # Default separators covering most international formats
    DEFAULT_SEPARATORS = ["-", "/", ".", " ", "_"]
    
    def __init__(
        self,
        date_fields: Optional[List[str]] = None,
        separators: Optional[List[str]] = None,
        output_format: str = "%Y-%m-%d",
        include_long_months: bool = True,
        min_year: int = 1900,
        max_year: int = 2100,
    ):
        """
        Initialize the date postprocessor.
        
        Args:
            date_fields: Specific field names to process. If None, auto-detects
                fields containing "date" in their name.
            separators: List of separator characters to use for format generation.
                Defaults to ["-", "/", ".", " ", "_"].
            output_format: strftime pattern for output. Defaults to ISO format.
            include_long_months: Include text month formats (January, Jan).
            min_year: Minimum acceptable year (dates outside range are rejected).
            max_year: Maximum acceptable year.
        """
        self.date_fields = date_fields
        self.separators = separators or self.DEFAULT_SEPARATORS
        self.output_format = output_format
        self.include_long_months = include_long_months
        self.min_year = min_year
        self.max_year = max_year
        
        # Generate all format combinations
        self._formats = _generate_date_formats(
            self.separators, 
            self.include_long_months
        )
    
    @property
    def formats(self) -> List[str]:
        """Get all generated date formats."""
        return self._formats
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize date fields in the data.
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            Data with normalized date fields
        """
        result = data.copy()
        
        fields_to_process = self._get_fields_to_process(data)
        
        for field in fields_to_process:
            value = data.get(field)
            if value is None or value == "":
                continue
                
            normalized = self._normalize_date(value)
            if normalized is not None:
                result[field] = normalized
        
        return result
    
    def _get_fields_to_process(self, data: Dict[str, Any]) -> List[str]:
        """Determine which fields to process."""
        if self.date_fields:
            return [f for f in self.date_fields if f in data]
        
        # Auto-detect: fields with "date" in name
        return [k for k in data.keys() if "date" in k.lower()]
    
    def _normalize_date(self, value: Any) -> Optional[str]:
        """Try to parse and normalize a date value."""
        if not isinstance(value, str):
            return None
        
        value = value.strip()
        if not value:
            return None
        
        for fmt in self._formats:
            try:
                parsed = datetime.strptime(value, fmt)
                
                # Validate year range
                if parsed.year < self.min_year or parsed.year > self.max_year:
                    continue
                
                return parsed.strftime(self.output_format)
            except ValueError:
                continue
        
        return None
