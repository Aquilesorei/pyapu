"""
Extractor plugins for document-to-text conversion.

These plugins wrap the existing extraction functionality as pluggable components.
"""

from .pdf import PDFExtractor
from .image import ImageExtractor
from .excel import ExcelExtractor
from .formatted import FormattedDocExtractor
from .gliner import GlinerExtractor

__all__ = [
    "PDFExtractor",
    "ImageExtractor", 
    "ExcelExtractor",
    "FormattedDocExtractor",
    "GlinerExtractor",
    "get_extractor",
]


def get_extractor(mime_type: str):
    """
    Get the appropriate extractor for a MIME type.
    
    Args:
        mime_type: MIME type of the document
        
    Returns:
        An extractor instance that can handle the MIME type
        
    Raises:
        ValueError: If no extractor can handle the MIME type
    """
    extractors = [PDFExtractor(), ImageExtractor(), ExcelExtractor()]
    
    for extractor in extractors:
        if extractor.can_handle(mime_type):
            return extractor
    
    raise ValueError(f"No extractor available for MIME type: {mime_type}")
