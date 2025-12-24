from enum import StrEnum


class PluginType(StrEnum):
    """Enumeration of supported plugin types.

    Used for type-safe plugin type references throughout the codebase,
    plugin registry lookups, entry point group names, and CLI commands.

    Example:
        >>> PluginType.PROVIDER
        'provider'
        >>> PluginType.PROVIDER == "provider"
        True
    """
    PROVIDER = "provider"
    EXTRACTOR = "extractor"
    VALIDATOR = "validator"
    POSTPROCESSOR = "postprocessor"
    SECURITY = "security"
