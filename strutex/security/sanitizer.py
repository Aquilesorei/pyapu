"""
Input sanitization security plugin.
"""

import re
import unicodedata
from typing import Optional

from ..plugins.base import SecurityPlugin, SecurityResult


class InputSanitizer(SecurityPlugin):
    """
    Sanitizes input text to prevent various attacks.
    
    Features:
    - Collapse excessive whitespace
    - Normalize Unicode characters
    - Remove invisible characters
    - Limit input length
    
    Usage:
        sanitizer = InputSanitizer(collapse_whitespace=True, max_length=50000)
        result = sanitizer.validate_input(text)
    """
    
    def __init__(
        self,
        collapse_whitespace: bool = True,
        normalize_unicode: bool = True,
        remove_invisible: bool = True,
        max_length: Optional[int] = None
    ):
        self.collapse_whitespace = collapse_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_invisible = remove_invisible
        self.max_length = max_length
    
    def validate_input(self, text: str) -> SecurityResult:
        """Sanitize the input text."""
        sanitized = text
        
        # Normalize Unicode (NFC form)
        if self.normalize_unicode:
            sanitized = unicodedata.normalize("NFC", sanitized)
        
        # Remove invisible characters (zero-width, etc.)
        if self.remove_invisible:
            # Remove zero-width characters and other invisibles
            invisible_pattern = r'[\u200b\u200c\u200d\u2060\u2061\u2062\u2063\u2064\ufeff]'
            sanitized = re.sub(invisible_pattern, '', sanitized)
        
        # Collapse whitespace (multiple spaces/newlines → single)
        if self.collapse_whitespace:
            # Collapse multiple spaces to single
            sanitized = re.sub(r' {2,}', ' ', sanitized)
            # Collapse multiple newlines to double (preserve paragraphs)
            sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
            # Remove trailing whitespace per line
            sanitized = re.sub(r' +$', '', sanitized, flags=re.MULTILINE)
        
        # Enforce max length
        if self.max_length and len(sanitized) > self.max_length:
            return SecurityResult(
                valid=False,
                text=None,
                reason=f"Input exceeds maximum length of {self.max_length} characters"
            )
        
        return SecurityResult(valid=True, text=sanitized)
