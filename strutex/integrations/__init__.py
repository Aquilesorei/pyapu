# strutex/integrations/__init__.py
"""
Framework integrations for Strutex.

Provides compatibility layers for LangChain, LlamaIndex, Haystack
and Unstructured.io fallback.
"""

__all__ = []

# LangChain integration
try:
    from .langchain import StrutexLoader, StrutexOutputParser
    __all__.extend(["StrutexLoader", "StrutexOutputParser"])
except ImportError:
    pass

# LlamaIndex integration
try:
    from .llamaindex import StrutexReader, StrutexNodeParser
    __all__.extend(["StrutexReader", "StrutexNodeParser"])
except ImportError:
    pass

# Haystack integration
try:
    from .haystack import StrutexConverter
    __all__.extend(["StrutexConverter"])
except ImportError:
    pass

# Unstructured Fallback
try:
    from .unstructured import UnstructuredFallbackProcessor
    __all__.extend(["UnstructuredFallbackProcessor"])
except ImportError:
    pass