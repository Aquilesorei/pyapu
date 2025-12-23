"""
Protocol-typed interfaces for pyapu plugins.

Provides runtime-checkable Protocol classes that define the expected interface
for all plugin types. These enable mypy type checking and runtime validation
of plugin compliance.

Example:
    >>> from pyapu.plugins.protocol import ProviderProtocol
    >>> isinstance(my_provider, ProviderProtocol)
    True
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

# Plugin API version for compatibility checks
PLUGIN_API_VERSION = "1.0"


@runtime_checkable
class ProviderProtocol(Protocol):
    """
    All provider plugins must implement this interface to be considered
    compliant with the pyapu plugin system.
    
    Attributes:
        pyapu_plugin_version: API version string (e.g., "1.0")
        priority: Ordering priority (0-100, higher = preferred)
        cost: Cost hint for optimization (lower = cheaper)
        capabilities: List of supported features (e.g., ["vision", "batch"])
    """
    
    pyapu_plugin_version: str
    priority: int
    cost: float
    capabilities: List[str]
    
    def process(
        self,
        file_path: str,
        prompt: str,
        schema: Any,
        mime_type: str,
        **kwargs: Any
    ) -> Any:
        """Process a document and extract structured data."""
        ...
    
    @classmethod
    def health_check(cls) -> bool:
        """Return True if plugin is healthy and ready."""
        ...


@runtime_checkable
class ExtractorProtocol(Protocol):
    """
    Extractors convert raw document bytes into text or structured
    content that can be sent to an LLM.
    
    Attributes:
        pyapu_plugin_version: API version string
        priority: Ordering priority for waterfall chains
        supported_mime_types: List of MIME types this extractor handles
    """
    
    pyapu_plugin_version: str
    priority: int
    supported_mime_types: List[str]
    
    def extract(self, file_path: str) -> str:
        """Extract text content from a document."""
        ...
    
    def can_handle(self, mime_type: str) -> bool:
        """Check if this extractor can handle the given MIME type."""
        ...
    
    @classmethod
    def health_check(cls) -> bool:
        """Return True if plugin is healthy and ready."""
        ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    """
    Validators check extracted data for correctness and can
    optionally fix issues.
    
    Attributes:
        pyapu_plugin_version: API version string
        priority: Ordering priority in validation chain
    """
    
    pyapu_plugin_version: str
    priority: int
    
    def validate(
        self,
        data: Dict[str, Any],
        schema: Optional[Any] = None
    ) -> Any:
        """Validate extracted data."""
        ...
    
    @classmethod
    def health_check(cls) -> bool:
        """Return True if plugin is healthy and ready."""
        ...


@runtime_checkable
class PostprocessorProtocol(Protocol):
    """
    Postprocessors transform extracted data (e.g., normalize dates,
    convert currencies, standardize units).
    
    Attributes:
        pyapu_plugin_version: API version string
        priority: Ordering priority in postprocessing pipeline
    """
    
    pyapu_plugin_version: str
    priority: int
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process/transform the extracted data."""
        ...
    
    @classmethod
    def health_check(cls) -> bool:
        """Return True if plugin is healthy and ready."""
        ...


@runtime_checkable
class SecurityPluginProtocol(Protocol):
    """
    Security plugins can validate/sanitize input before sending
    to the LLM and validate output before returning to the user.
    
    Attributes:
        pyapu_plugin_version: API version string
        priority: Ordering priority in security chain
    """
    
    pyapu_plugin_version: str
    priority: int
    
    def validate_input(self, text: str) -> Any:
        """Validate/sanitize input text before sending to LLM."""
        ...
    
    def validate_output(self, data: Dict[str, Any]) -> Any:
        """Validate output data before returning to user."""
        ...
    
    @classmethod
    def health_check(cls) -> bool:
        """Return True if plugin is healthy and ready."""
        ...


def check_plugin_version(plugin: Any) -> bool:
    """
    Check if a plugin's API version is compatible.
    
    Args:
        plugin: A plugin class or instance
        
    Returns:
        True if compatible, False otherwise
    """
    version = getattr(plugin, "pyapu_plugin_version", None)
    if version is None:
        return False
    
    # For now, only exact match. Future: semantic versioning
    return version == PLUGIN_API_VERSION


def validate_plugin_protocol(plugin: Any, expected_protocol: type) -> bool:
    """
    Validate that a plugin implements the expected protocol.
    
    Args:
        plugin: A plugin class or instance
        expected_protocol: The Protocol class to check against
        
    Returns:
        True if plugin implements the protocol
    """
    return isinstance(plugin, expected_protocol)
