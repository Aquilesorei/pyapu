"""
Postprocessor plugins for data transformation.

Postprocessors normalize and transform extracted data after LLM processing.
Common use cases include date normalization, number parsing, and currency conversion.

Example:
    from strutex.postprocessors import DatePostprocessor, NumberPostprocessor
    
    processor = DocumentProcessor(
        provider="gemini",
        postprocessors=[
            DatePostprocessor(),
            NumberPostprocessor(),
        ]
    )
"""

from .date import DatePostprocessor
from .number import NumberPostprocessor
from .currency import CurrencyNormalizer
from .chain import PostprocessorChain

__all__ = [
    "DatePostprocessor",
    "NumberPostprocessor",
    "CurrencyNormalizer",
    "PostprocessorChain",
]
