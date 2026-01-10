"""
Processor implementations for strutex.

This module provides strategy-specific processor classes:
- SimpleProcessor: Single LLM call extraction
- VerifiedProcessor: Extraction with verification loop
- RagProcessor: Retrieval-Augmented Generation
- BatchProcessor: Parallel document processing
- FallbackProcessor: Multi-provider retry logic
- RouterProcessor: Content-based document routing
- EnsembleProcessor: Multi-provider consensus
- SequentialProcessor: Page-by-page state preservation
- PrivacyProcessor: PII redaction and restoration
- ActiveLearningProcessor: Confidence scoring and human-in-the-loop flagging
"""

from .base import Processor
from .simple import SimpleProcessor
from .verified import VerifiedProcessor
from .rag import RagProcessor
from .batch import BatchProcessor
from .fallback import FallbackProcessor
from .router import RouterProcessor
from .ensemble import EnsembleProcessor
from .sequential import SequentialProcessor
from .privacy import PrivacyProcessor
from .active import ActiveLearningProcessor
from .agentic import AgenticProcessor

__all__ = [
    "Processor",
    "SimpleProcessor",
    "VerifiedProcessor",
    "RagProcessor",
    "BatchProcessor",
    "FallbackProcessor",
    "RouterProcessor",
    "EnsembleProcessor",
    "SequentialProcessor",
    "PrivacyProcessor",
    "ActiveLearningProcessor",
    "AgenticProcessor",
]
