"""
Base provider class for LLM providers.

Re-exports Provider from plugins.base for convenience.
"""

# Single source of truth - Provider is defined in plugins.base
from ..plugins.base import Provider

__all__ = ["Provider"]
