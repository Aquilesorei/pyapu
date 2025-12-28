"""
GLiNER Extractor for fast local entity extraction.

Uses GLiNER (Generalist and Lightweight Named Entity Recognition) for 
zero-shot entity extraction without LLM API calls.

This is useful for:
- Fast preprocessing before LLM refinement
- Reducing LLM costs by pre-extracting simple entities
- Fully local/offline entity extraction

Install: pip install gliner
"""

import logging
from typing import Any, Dict, List, Optional

from ..plugins.base import Extractor

logger = logging.getLogger("strutex.extractors.gliner")

# Lazy import GLiNER
GLINER_AVAILABLE = False
try:
    from gliner import GLiNER
    GLINER_AVAILABLE = True
except ImportError:
    GLiNER = None


# Default entity labels for common document extraction
DEFAULT_LABELS = [
    "person",
    "organization", 
    "company",
    "date",
    "money",
    "amount",
    "address",
    "phone",
    "email",
    "invoice_number",
    "order_number",
    "product",
    "quantity",
]


class GlinerExtractor(Extractor, name="gliner"):
    """
    Fast local entity extraction using GLiNER.
    
    GLiNER is a zero-shot NER model that can extract custom entities
    without fine-tuning. It's much faster than LLM calls and runs locally.
    
    Use cases:
        - Pre-extract entities before LLM for cost reduction
        - Fast local extraction for simple documents
        - Hybrid pipeline: GLiNER for entities, LLM for reasoning
    
    Example:
        ```python
        from strutex.extractors import GlinerExtractor
        
        # Extract with default labels
        extractor = GlinerExtractor()
        result = extractor.extract("invoice.pdf")
        
        # Custom labels for your domain
        extractor = GlinerExtractor(labels=["container_id", "vessel", "port"])
        result = extractor.extract("bill_of_lading.pdf")
        ```
    
    Attributes:
        model_name: GLiNER model to use (default: urchade/gliner_base)
        labels: Entity labels to extract
        threshold: Confidence threshold for entity detection (0-1)
    """
    
    priority = 70  # Higher priority for speed
    supported_mime_types = [
        "application/pdf",
        "text/plain",
        "text/csv",
    ]
    
    def __init__(
        self,
        model_name: str = "urchade/gliner_base",
        labels: Optional[List[str]] = None,
        threshold: float = 0.3,
        include_text: bool = True,
    ):
        """
        Initialize GLiNER extractor.
        
        Args:
            model_name: HuggingFace model name for GLiNER.
                Options: urchade/gliner_small, urchade/gliner_base, urchade/gliner_large
            labels: Entity labels to extract. If None, uses default labels.
            threshold: Confidence threshold (0-1). Lower = more entities, higher = more precise.
            include_text: If True, includes original text with entity annotations.
        """
        self.model_name = model_name
        self.labels = labels or DEFAULT_LABELS
        self.threshold = threshold
        self.include_text = include_text
        self._model: Optional[Any] = None
    
    @property
    def model(self):
        """Lazy load GLiNER model."""
        if self._model is None:
            if not GLINER_AVAILABLE:
                raise ImportError(
                    "GLiNER is required for GlinerExtractor. "
                    "Install with: pip install gliner"
                )
            logger.info(f"Loading GLiNER model: {self.model_name}")
            self._model = GLiNER.from_pretrained(self.model_name)
        return self._model
    
    def extract(self, file_path: str) -> str:
        """
        Extract entities from a document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Formatted string with extracted entities and optional source text.
            Format is designed to be easily parsed by LLMs for refinement.
        """
        # First extract text from the document
        text = self._get_text(file_path)
        
        if not text.strip():
            return ""
        
        # Run GLiNER entity extraction
        entities = self._extract_entities(text)
        
        # Format output for LLM consumption
        return self._format_output(text, entities)
    
    def _get_text(self, file_path: str) -> str:
        """Extract raw text from file."""
        import os
        
        mime_type = self._detect_mime_type(file_path)
        
        if mime_type == "application/pdf":
            return self._extract_pdf_text(file_path)
        elif mime_type in ("text/plain", "text/csv"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")
    
    def _detect_mime_type(self, file_path: str) -> str:
        """Detect MIME type from file extension."""
        import os
        ext = os.path.splitext(file_path)[1].lower()
        
        mime_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".csv": "text/csv",
        }
        return mime_map.get(ext, "application/octet-stream")
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF using available libraries."""
        # Try PyMuPDF first (faster)
        try:
            import fitz
            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n\n".join(text_parts)
        except ImportError:
            pass
        
        # Fall back to pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return "\n\n".join(text_parts)
        except ImportError:
            raise ImportError(
                "PDF extraction requires PyMuPDF or pdfplumber. "
                "Install with: pip install pymupdf or pip install pdfplumber"
            )
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Run GLiNER entity extraction."""
        # GLiNER has a max text length, chunk if needed
        max_length = 4096
        
        if len(text) <= max_length:
            return self.model.predict_entities(
                text, 
                self.labels,
                threshold=self.threshold
            )
        
        # Chunk text and extract from each chunk
        all_entities = []
        chunks = self._chunk_text(text, max_length)
        
        for i, chunk in enumerate(chunks):
            chunk_entities = self.model.predict_entities(
                chunk["text"],
                self.labels,
                threshold=self.threshold
            )
            # Adjust positions based on chunk offset
            for entity in chunk_entities:
                entity["start"] += chunk["offset"]
                entity["end"] += chunk["offset"]
                entity["chunk"] = i
            all_entities.extend(chunk_entities)
        
        return all_entities
    
    def _chunk_text(self, text: str, max_length: int) -> List[Dict[str, Any]]:
        """Split text into chunks with overlap."""
        chunks = []
        overlap = 200
        start = 0
        
        while start < len(text):
            end = min(start + max_length, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = text.rfind(".", start, end)
                if last_period > start + max_length // 2:
                    end = last_period + 1
            
            chunks.append({
                "text": text[start:end],
                "offset": start,
            })
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def _format_output(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """Format extracted entities for LLM consumption."""
        lines = ["[EXTRACTED ENTITIES]"]
        
        # Group entities by label
        by_label: Dict[str, List[str]] = {}
        for entity in entities:
            label = entity["label"]
            value = entity["text"]
            score = entity.get("score", 0)
            
            if label not in by_label:
                by_label[label] = []
            by_label[label].append(f"{value} (confidence: {score:.2f})")
        
        # Format grouped entities
        for label, values in sorted(by_label.items()):
            unique_values = list(dict.fromkeys(values))  # Dedupe while preserving order
            lines.append(f"\n{label.upper()}:")
            for value in unique_values[:10]:  # Limit to top 10 per label
                lines.append(f"  - {value}")
        
        # Optionally include source text
        if self.include_text:
            lines.append("\n\n[SOURCE TEXT]")
            lines.append(text[:8000])  # Limit text length
            if len(text) > 8000:
                lines.append(f"\n... (truncated, {len(text)} total characters)")
        
        return "\n".join(lines)
    
    def extract_structured(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract entities as structured data (not formatted string).
        
        Returns:
            Dict mapping label names to lists of entity dicts.
            Each entity has: text, start, end, score
        """
        text = self._get_text(file_path)
        entities = self._extract_entities(text)
        
        # Group by label
        result: Dict[str, List[Dict[str, Any]]] = {}
        for entity in entities:
            label = entity["label"]
            if label not in result:
                result[label] = []
            result[label].append({
                "text": entity["text"],
                "start": entity["start"],
                "end": entity["end"],
                "score": entity.get("score", 0),
            })
        
        return result
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if GLiNER is available."""
        return GLINER_AVAILABLE
