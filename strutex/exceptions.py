"""
Strutex exception hierarchy.

Provides specific exception types for different failure modes,
enabling precise error handling and better debugging.

Example:
    >>> from strutex.exceptions import ProviderError, ValidationError
    >>> 
    >>> try:
    ...     result = processor.process("doc.pdf", "Extract")
    ... except ProviderError as e:
    ...     print(f"LLM failed: {e}")
    ... except ValidationError as e:
    ...     print(f"Output invalid: {e}")
"""

from typing import Any, Dict, List, Optional


class StrutexError(Exception):
    """
    Base exception for all Strutex errors.
    
    All Strutex-specific exceptions inherit from this class,
    allowing catch-all handling:
    
        try:
            processor.process(...)
        except StrutexError as e:
            # Handle any Strutex error
            log.error(f"Strutex failed: {e}")
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


# --- Provider Errors ---

class ProviderError(StrutexError):
    """
    Error from an LLM provider (API failure, rate limit, etc.).
    
    Attributes:
        provider: Name of the provider that failed
        status_code: HTTP status code if applicable
        retryable: Whether the error is likely transient
    """
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable


class RateLimitError(ProviderError):
    """
    Rate limit exceeded on provider API.
    
    Attributes:
        retry_after: Seconds to wait before retrying (if provided by API)
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        provider: Optional[str] = None,
        retry_after: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, provider, status_code=429, retryable=True, details=details)
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Invalid or missing API credentials."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, provider, status_code=401, retryable=False, details=details)


class ModelNotFoundError(ProviderError):
    """Requested model not available."""
    
    def __init__(
        self,
        model: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Model '{model}' not found"
        super().__init__(message, provider, status_code=404, retryable=False, details=details)
        self.model = model


# --- Extraction Errors ---

class ExtractionError(StrutexError):
    """
    Failed to extract structured data from document.
    
    Attributes:
        file_path: Path to the document that failed
        stage: Stage where extraction failed (e.g., "parsing", "llm", "validation")
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.file_path = file_path
        self.stage = stage


class DocumentParseError(ExtractionError):
    """Failed to parse/read the input document."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        mime_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, file_path, stage="parsing", details=details)
        self.mime_type = mime_type


class SchemaError(ExtractionError):
    """Invalid or incompatible schema definition."""
    
    def __init__(
        self,
        message: str,
        schema_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, stage="schema", details=details)
        self.schema_type = schema_type


# --- Validation Errors ---

class ValidationError(StrutexError):
    """
    Extracted data failed validation.
    
    Attributes:
        issues: List of validation issues found
        data: The data that failed validation
    """
    
    def __init__(
        self,
        message: str,
        issues: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.issues = issues or []
        self.data = data
    
    def __str__(self) -> str:
        if self.issues:
            issues_str = "; ".join(self.issues[:3])
            if len(self.issues) > 3:
                issues_str += f" (+{len(self.issues) - 3} more)"
            return f"{self.message}: {issues_str}"
        return self.message


class SchemaValidationError(ValidationError):
    """Output doesn't match expected schema structure."""
    pass


class DateValidationError(ValidationError):
    """Date field validation failed."""
    pass


class SumValidationError(ValidationError):
    """Sum/total validation failed."""
    pass


# --- Configuration Errors ---

class ConfigurationError(StrutexError):
    """Invalid configuration or setup."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.config_key = config_key


class PluginError(ConfigurationError):
    """Plugin loading or execution failed."""
    
    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.plugin_name = plugin_name
        self.plugin_type = plugin_type


# --- Cache Errors ---

class CacheError(StrutexError):
    """Cache operation failed."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,  # "get", "set", "delete"
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.operation = operation


# --- Security Errors ---

class SecurityError(StrutexError):
    """Security check failed."""
    pass


class InjectionDetectedError(SecurityError):
    """Potential prompt injection detected."""
    
    def __init__(
        self,
        message: str = "Potential prompt injection detected",
        pattern: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.pattern = pattern


# --- Timeout Errors ---

class TimeoutError(StrutexError):
    """Operation timed out."""
    
    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds


# Convenience exports
__all__ = [
    # Base
    "StrutexError",
    
    # Provider
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "ModelNotFoundError",
    
    # Extraction
    "ExtractionError",
    "DocumentParseError",
    "SchemaError",
    
    # Validation
    "ValidationError",
    "SchemaValidationError",
    "DateValidationError",
    "SumValidationError",
    
    # Config
    "ConfigurationError",
    "PluginError",
    
    # Cache
    "CacheError",
    
    # Security
    "SecurityError",
    "InjectionDetectedError",
    
    # Timeout
    "TimeoutError",
]
