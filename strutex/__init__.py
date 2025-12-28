"""
strutex - Structured AI Document Processing

Extract structured JSON from documents using LLMs.
"""

# Schema types
from .types import Schema, Type
from .types import String, Number, Integer, Boolean, Array, Object, Enum, Date, DateTime

# Processor
from .processor import DocumentProcessor

# Exceptions
from .exceptions import (
    StrutexError,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    ExtractionError,
    ValidationError,
    ConfigurationError,
    PluginError,
    CacheError,
    SecurityError,
    InjectionDetectedError,
)

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

# Extractors
from .extractors import (
    PDFExtractor,
    ImageExtractor,
    ExcelExtractor,
    FormattedDocExtractor,
    get_extractor,
)

# Validators
from .validators import (
    SchemaValidator,
    SumValidator,
    DateValidator,
    ValidationChain,
)

# Providers
from .providers import (
    GeminiProvider,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
    GroqProvider,
    LangdockProvider,
    HybridProvider,
    HybridStrategy,
    ProviderChain,
    RetryConfig,
    local_first_chain,
    cost_optimized_chain,
    StreamingProcessor,
)

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

# Logging
from .logging import get_logger, configure_logging, set_level

# Context (stateful workflows)
from .context import ProcessingContext, BatchContext

# Input handling (file paths and BytesIO)
from .input import DocumentInput

# Cache
from .cache import MemoryCache, SQLiteCache, FileCache, CacheKey

# Schemas (ready-to-use Pydantic models)
from . import schemas

# Integrations (LangChain, LlamaIndex)
from . import integrations

# Type hints
from typing import Any, Dict, Optional, Union, TYPE_CHECKING, Type as TypingType
if TYPE_CHECKING:
    from pydantic import BaseModel


def extract(
    document: str,
    schema: Optional[Union["Schema", "Type"]] = None,
    *,
    provider: str = "gemini",
    prompt: str = "Extract the data from this document.",
    model: Optional[TypingType["BaseModel"]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Extract structured data from a document. That's it.
    
    This is the simplest way to use strutex. Everything else is optional.
    
    Args:
        document: Path to the document (PDF, image, Excel, etc.)
        schema: Schema definition for extraction (native Schema/Type)
        provider: LLM provider name ("gemini", "openai", "anthropic", "ollama")
        prompt: Extraction instructions
        model: Pydantic model for extraction (alternative to schema)
        **kwargs: Additional options passed to DocumentProcessor.process()
    
    Returns:
        Extracted data as a dictionary (or Pydantic model if `model` was used)
    
    Example:
        >>> import strutex
        >>> result = strutex.extract("invoice.pdf", InvoiceSchema)
        >>> print(result["total"])
        1250.00
        
        # Or with Pydantic:
        >>> invoice = strutex.extract("invoice.pdf", model=Invoice)
        >>> print(invoice.total)
    """
    processor = DocumentProcessor(provider=provider)
    return processor.process(
        file_path=document,
        prompt=prompt,
        schema=schema,
        model=model,
        **kwargs
    )


__all__ = [
    # Core
    "extract",
    "DocumentProcessor",
    "StructuredPrompt",
    
    # Exceptions
    "StrutexError",
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "ExtractionError",
    "ValidationError",
    "ConfigurationError",
    "PluginError",
    "CacheError",
    "SecurityError",
    "InjectionDetectedError",
    
    # Schema types
    "Schema",
    "Type",
    "String",
    "Number",
    "Integer",
    "Boolean",
    "Array",
    "Object",
    "Enum",
    "Date",
    "DateTime",
    
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
    
    # Extractors
    "PDFExtractor",
    "ImageExtractor",
    "ExcelExtractor",
    "get_extractor",
    
    # Validators
    "SchemaValidator",
    "SumValidator",
    "DateValidator",
    "ValidationChain",
    
    # Providers
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "GroqProvider",
    "LangdockProvider",
    "HybridProvider",
    "HybridStrategy",
    "ProviderChain",
    "RetryConfig",
    "local_first_chain",
    "cost_optimized_chain",
    
    # Security
    "SecurityChain",
    "InputSanitizer",
    "PromptInjectionDetector",
    "OutputValidator",
    "default_security_chain",
    
    # Pydantic
    "pydantic_to_schema",
    "validate_with_pydantic",
    
    # Logging
    "get_logger",
    "configure_logging",
    "set_level",
    
    # Context (stateful workflows)
    "ProcessingContext",
    "BatchContext",
    "StreamingProcessor",
    
    # Cache
    "MemoryCache",
    "SQLiteCache",
    "FileCache",
    "CacheKey",
    
    # Input handling
    "DocumentInput",
    
    # Schemas module
    "schemas",
    
    # Integrations module
    "integrations",
]