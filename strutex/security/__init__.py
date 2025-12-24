"""
Security layer for strutex.

Provides pluggable security plugins for input sanitization,
prompt injection detection, and output validation.
"""

from ..plugins.base import SecurityPlugin, SecurityResult
from .sanitizer import InputSanitizer
from .injection import PromptInjectionDetector
from .output import OutputValidator
from .chain import SecurityChain, default_security_chain

__all__ = [
    "SecurityPlugin",
    "SecurityResult",
    "InputSanitizer",
    "PromptInjectionDetector",
    "OutputValidator",
    "SecurityChain",
    "default_security_chain"
]
