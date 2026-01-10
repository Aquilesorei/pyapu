"""
Logging configuration for strutex.

Provides a standardized logging setup with configurable handlers and levels.
All strutex components should use `get_logger(__name__)` to obtain their logger.

Example:
    >>> from strutex.log_utils import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing document")
    
    # Configure logging level
    >>> from strutex.log_utils import configure_logging
    >>> configure_logging(level="DEBUG")
"""

import logging
import os
import sys
from typing import Optional


# Default format for strutex logs
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(levelname)s: %(message)s"

# Root logger name
ROOT_LOGGER_NAME = "strutex"

# Module-level logger cache
_loggers: dict = {}
_configured = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the given module name.
    
    Uses a hierarchical naming scheme under 'strutex.*' for consistent
    log filtering and configuration.
    
    Args:
        name: Module name (typically `__name__`)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting extraction")
    """
    # Ensure name is under strutex hierarchy
    if not name.startswith(ROOT_LOGGER_NAME):
        name = f"{ROOT_LOGGER_NAME}.{name}"
    
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger
        
        # Configure on first access if not already done
        if not _configured:
            configure_logging()
    
    return _loggers[name]


def configure_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    handler: Optional[logging.Handler] = None,
    force: bool = False
) -> logging.Logger:
    """
    Configure logging for all strutex components.
    
    This should be called once at application startup if you want to
    customize logging. Otherwise, default configuration is applied
    automatically on first logger access.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            Can also be set via STRUTEX_LOG_LEVEL environment variable.
        format_string: Custom format string for log messages.
            Defaults to timestamp, logger name, level, and message.
        handler: Custom logging handler. Defaults to StreamHandler(stderr).
        force: If True, reconfigure even if already configured.
        
    Returns:
        The root strutex logger
        
    Example:
        >>> configure_logging(level="DEBUG")
        >>> configure_logging(
        ...     level="INFO",
        ...     format_string="%(levelname)s - %(message)s"
        ... )
    """
    global _configured
    
    if _configured and not force:
        return logging.getLogger(ROOT_LOGGER_NAME)
    
    # Get level from environment if not specified
    env_level = os.environ.get("STRUTEX_LOG_LEVEL", "").upper()
    if env_level and level == "INFO":  # Only use env if level is default
        level = env_level
    
    # Get the root strutex logger
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers if reconfiguring
    if force:
        root_logger.handlers.clear()
    
    # Add handler if none exist
    if not root_logger.handlers:
        if handler is None:
            handler = logging.StreamHandler(sys.stderr)
        
        # Set format
        if format_string is None:
            format_string = DEFAULT_FORMAT
        
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    
    # Prevent propagation to root logger
    root_logger.propagate = False
    
    _configured = True
    return root_logger


def set_level(level: str) -> None:
    """
    Set the logging level for all strutex loggers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Example:
        >>> set_level("DEBUG")  # Enable debug logging
        >>> set_level("WARNING")  # Reduce verbosity
    """
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))


def disable_logging() -> None:
    """
    Disable all strutex logging.
    
    Useful for library usage where the consuming application
    wants to manage its own logging.
    """
    logging.getLogger(ROOT_LOGGER_NAME).disabled = True


def enable_logging() -> None:
    """Re-enable strutex logging after it was disabled."""
    logging.getLogger(ROOT_LOGGER_NAME).disabled = False
