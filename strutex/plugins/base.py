"""
Abstract base classes for all plugin types.

Subclassing these base classes auto-registers plugins with the PluginRegistry.
Abstract classes (with unimplemented @abstractmethod) are NOT registered.

Example:
    >>> class MyProvider(Provider):
    ...     def process(self, ...): ...
    # Auto-registered as "myprovider"
    
    >>> class CustomProvider(Provider, name="custom", priority=90):
    ...     def process(self, ...): ...
    # Auto-registered as "custom" with priority 90
    
    >>> class BaseProvider(Provider, register=False):
    ...     pass
    # NOT registered (explicit opt-out)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from .plugin_type import PluginType
from ..types import Schema


def _auto_register(
    cls,
    plugin_type: str,
    name: Optional[str] = None,
    register: bool = True,
    **kwargs
) -> None:
    """
    Helper to auto-register a plugin class via __init_subclass__.
    
    Skips registration if:
    - register=False (explicit opt-out)
    - Class still has abstract methods (intermediate base class)
    """
    if not register:
        return
    
    # Check if class is still abstract by looking for unimplemented abstract methods.
    # We can't use __abstractmethods__ directly because it's not set yet when
    # __init_subclass__ is called. Instead, we check if any parent's abstract
    # methods are NOT overridden in this class's own __dict__.
    for base in cls.__mro__[1:]:  # Skip cls itself
        for attr_name in getattr(base, "__abstractmethods__", ()):
            # Check if this class provides its own implementation
            if attr_name not in cls.__dict__:
                # Still abstract - don't register
                return
    
    from .registry import PluginRegistry
    
    plugin_name = name or cls.__name__.lower()
    PluginRegistry.register(plugin_type, plugin_name, cls)


class Provider(ABC):
    """
    Base class for LLM providers.
    
    All providers must implement the process method to handle
    document extraction via their specific LLM API.
    
    Subclassing auto-registers the plugin. Use class arguments to customize:
    
        class MyProvider(Provider, name="custom", priority=90):
            ...
    
    Attributes:
        strutex_plugin_version: API version for compatibility checks
        priority: Ordering priority (0-100, higher = preferred)
        cost: Cost hint for optimization (lower = cheaper)
        capabilities: List of supported features
    """
    
    # Plugin API version (required for compatibility checks)
    strutex_plugin_version: str = "1.0"
    
    # Priority for waterfall ordering (0-100, higher = preferred)
    priority: int = 50
    
    # Cost hint for optimization (lower = cheaper)
    cost: float = 1.0
    
    # Declare capabilities (override in subclasses)
    capabilities: List[str] = []
    
    def __init_subclass__(
        cls,
        name: Optional[str] = None,
        register: bool = True,
        **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        _auto_register(cls, PluginType.PROVIDER, name=name, register=register)
    
    @abstractmethod
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """
        Process a document and extract structured data.
        
        Args:
            file_path: Path to the document file
            prompt: Extraction prompt/instructions
            schema: Expected output schema
            mime_type: MIME type of the file
            **kwargs: Provider-specific options
            
        Returns:
            Extracted data matching the schema
        """
        pass
    
    async def aprocess(
        self,
        file_path: str,
        prompt: str,
        schema: Schema,
        mime_type: str,
        **kwargs
    ) -> Any:
        """
        Async version of process. Override for true async support.
        Default implementation calls sync version.
        """
        return self.process(file_path, prompt, schema, mime_type, **kwargs)
    
    def has_capability(self, capability: str) -> bool:
        """Check if this provider has a specific capability."""
        return capability.lower() in [c.lower() for c in self.capabilities]
    
    @classmethod
    def health_check(cls) -> bool:
        """
        Check if this provider is healthy and ready to use.
        
        Override in subclasses for custom health checks (e.g., API connectivity).
        
        Returns:
            True if healthy, False otherwise
        """
        return True


class Extractor(ABC):
    """
    Base class for document extractors.
    
    Extractors convert raw document bytes into text or structured
    content that can be sent to an LLM.
    
    Subclassing auto-registers the plugin.
    
    Attributes:
        strutex_plugin_version: API version for compatibility checks
        priority: Ordering priority for waterfall chains
        supported_mime_types: List of MIME types this extractor handles
    """
    
    # Plugin API version
    strutex_plugin_version: str = "1.0"
    
    # Priority for waterfall ordering
    priority: int = 50
    
    # MIME types this extractor handles
    supported_mime_types: List[str] = []
    
    def __init_subclass__(
        cls,
        name: Optional[str] = None,
        register: bool = True,
        **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        _auto_register(cls, PluginType.EXTRACTOR, name=name, register=register)
    
    @abstractmethod
    def extract(self, file_path: str) -> str:
        """
        Extract text content from a document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Extracted text content
        """
        pass
    
    def can_handle(self, mime_type: str) -> bool:
        """Check if this extractor can handle the given MIME type."""
        return mime_type in self.supported_mime_types
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if this extractor is healthy and ready."""
        return True


class Validator(ABC):
    """
    Base class for output validators.
    
    Validators check extracted data for correctness and can
    optionally fix issues.
    
    Subclassing auto-registers the plugin.
    
    Attributes:
        strutex_plugin_version: API version for compatibility checks
        priority: Ordering priority in validation chain
    """
    
    # Plugin API version
    strutex_plugin_version: str = "1.0"
    
    # Priority in validation chain
    priority: int = 50
    
    def __init_subclass__(
        cls,
        name: Optional[str] = None,
        register: bool = True,
        **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        _auto_register(cls, PluginType.VALIDATOR, name=name, register=register)
    
    @abstractmethod
    def validate(self, data: Dict[str, Any], schema: Optional[Schema] = None) -> "ValidationResult":
        """
        Validate extracted data.
        
        Args:
            data: The extracted data to validate
            schema: Optional schema to validate against
            
        Returns:
            ValidationResult with status and any issues
        """
        pass
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if this validator is healthy and ready."""
        return True


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(
        self,
        valid: bool,
        data: Dict[str, Any],
        issues: Optional[list] = None,
        fixed: bool = False
    ):
        self.valid = valid
        self.data = data
        self.issues = issues or []
        self.fixed = fixed
    
    def __bool__(self) -> bool:
        return self.valid


class Postprocessor(ABC):
    """
    Base class for data postprocessors.
    
    Postprocessors transform extracted data (e.g., normalize dates,
    convert currencies, standardize units).
    
    Subclassing auto-registers the plugin.
    
    Attributes:
        strutex_plugin_version: API version for compatibility checks
        priority: Ordering priority in postprocessing pipeline
    """
    
    # Plugin API version
    strutex_plugin_version: str = "1.0"
    
    # Priority in postprocessing pipeline
    priority: int = 50
    
    def __init_subclass__(
        cls,
        name: Optional[str] = None,
        register: bool = True,
        **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        _auto_register(cls, PluginType.POSTPROCESSOR, name=name, register=register)
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process/transform the extracted data.
        
        Args:
            data: The data to transform
            
        Returns:
            Transformed data
        """
        pass
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if this postprocessor is healthy and ready."""
        return True


class SecurityPlugin(ABC):
    """
    Base class for security plugins.
    
    Security plugins can validate/sanitize input before sending
    to the LLM and validate output before returning to the user.
    
    Subclassing auto-registers the plugin.
    
    Attributes:
        strutex_plugin_version: API version for compatibility checks
        priority: Ordering priority in security chain
    """
    
    # Plugin API version
    strutex_plugin_version: str = "1.0"
    
    # Priority in security chain
    priority: int = 50
    
    def __init_subclass__(
        cls,
        name: Optional[str] = None,
        register: bool = True,
        **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        _auto_register(cls, PluginType.SECURITY, name=name, register=register)
    
    def validate_input(self, text: str) -> "SecurityResult":
        """
        Validate/sanitize input text before sending to LLM.
        
        Args:
            text: The input text (prompt + document content)
            
        Returns:
            SecurityResult with sanitized text or rejection
        """
        return SecurityResult(valid=True, text=text)
    
    def validate_output(self, data: Dict[str, Any]) -> "SecurityResult":
        """
        Validate output data before returning to user.
        
        Args:
            data: The extracted data
            
        Returns:
            SecurityResult with clean data or rejection
        """
        return SecurityResult(valid=True, data=data)
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if this security plugin is healthy and ready."""
        return True


class SecurityResult:
    """Result of a security check."""
    
    def __init__(
        self,
        valid: bool,
        text: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ):
        self.valid = valid
        self.text = text
        self.data = data
        self.reason = reason
    
    def __bool__(self) -> bool:
        return self.valid
