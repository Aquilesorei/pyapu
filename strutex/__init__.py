"""
strutex - Python AI PDF Utilities

Extract structured JSON from documents using LLMs.
"""

# Schema types
from .types import Schema, Type
from .types import String, Number, Integer, Boolean, Array, Object

# Processor
from .processor import DocumentProcessor, SecurityError

# Prompts
from .prompts import StructuredPrompt

# Document utilities
from .documents import (
    pdf_to_text,
    get_mime_type,
    encode_bytes_to_base64,
    read_file_as_bytes,
    excel_to_csv_sheets
)

# Plugin system
from .plugins import (
    PluginRegistry,
    register,
    Provider,
    Extractor,
    Validator,
    ValidationResult,
    Postprocessor,
    SecurityPlugin,
    SecurityResult
)

# Providers
from .providers import GeminiProvider

# Security
from .security import (
    SecurityChain,
    InputSanitizer,
    PromptInjectionDetector,
    OutputValidator,
    default_security_chain
)

# Pydantic support
from .pydantic_support import pydantic_to_schema, validate_with_pydantic

__all__ = [
    # Core
    "DocumentProcessor",
    "SecurityError",
    "StructuredPrompt",
    
    # Schema types
    "Schema",
    "Type",
    "String",
    "Number",
    "Integer",
    "Boolean",
    "Array",
    "Object",
    
    # Document utilities
    "pdf_to_text",
    "get_mime_type",
    "encode_bytes_to_base64",
    "read_file_as_bytes",
    "excel_to_csv_sheets",
    
    # Plugin system
    "PluginRegistry",
    "register",
    "Provider",
    "Extractor",
    "Validator",
    "ValidationResult",
    "Postprocessor",
    "SecurityPlugin",
    "SecurityResult",
    
    # Providers
    "GeminiProvider",
    
    # Security
    "SecurityChain",
    "InputSanitizer",
    "PromptInjectionDetector",
    "OutputValidator",
    "default_security_chain",
    
    # Pydantic
    "pydantic_to_schema",
    "validate_with_pydantic",
]