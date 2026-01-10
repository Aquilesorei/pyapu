"""
Provenance validator - verifies extracted data against source document.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from ..plugins.base import Validator, ValidationResult
from ..types import Schema
from ..similarity import compute_similarity

logger = logging.getLogger("strutex.validators.provenance")


class ProvenanceValidator(Validator, name="provenance"):
    """
    Validates that extracted values are grounded in the source document.
    
    Uses semantic similarity to check if extracted string values are
    present or semantically represented in the document text.
    
    Attributes:
        threshold: Similarity threshold (0.0 to 1.0)
        chunk_size: Size of text chunks for comparison
        exclude_fields: Fields to skip validation for
    """
    
    priority = 20  # Run after schema and other logic validators
    
    def __init__(
        self,
        threshold: float = 0.8,
        chunk_size: int = 500,
        exclude_fields: Optional[List[str]] = None
    ):
        """
        Initialize the provenance validator.
        
        Args:
            threshold: Similarity threshold to consider a match
            chunk_size: Character length of document chunks
            exclude_fields: Fields to ignore (e.g., calculated fields)
        """
        self.threshold = threshold
        self.chunk_size = chunk_size
        self.exclude_fields = exclude_fields or []
    
    def validate(
        self, 
        data: Dict[str, Any], 
        schema: Optional[Schema] = None,
        source_text: Optional[str] = None
    ) -> ValidationResult:
        """
        Verify that extracted data matches source text.
        
        Args:
            data: Extracted data
            schema: Optional extraction schema
            source_text: The original document text
            
        Returns:
            ValidationResult with any grounding issues
        """
        if not source_text:
            logger.debug("Skip provenance: no source text provided")
            return ValidationResult(valid=True, data=data)
            
        issues = []
        
        # Chunk text for better local matching
        chunks = self._chunk_text(source_text)
        
        # Recursively check fields
        self._check_data(data, chunks, "", issues)
        
        return ValidationResult(
            valid=len(issues) == 0,
            data=data,
            issues=issues
        )
        
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]
            
        chunks = []
        overlap = self.chunk_size // 4
        step = self.chunk_size - overlap
        
        for i in range(0, len(text), step):
            chunks.append(text[i:i + self.chunk_size])
            if i + self.chunk_size >= len(text):
                break
                
        return chunks
        
    def _check_data(
        self, 
        data: Any, 
        chunks: List[str], 
        path: str, 
        issues: List[str]
    ) -> None:
        """Recursively scan data for grounding issues."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in self.exclude_fields:
                    continue
                new_path = f"{path}.{key}" if path else key
                self._check_data(value, chunks, new_path, issues)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                self._check_data(item, chunks, new_path, issues)
        elif isinstance(data, str) and len(data.strip()) > 3:
            # Check grounding for meaningful strings
            if not self._is_grounded(data, chunks):
                issues.append(f"Provenance failure: '{path}' value '{data}' not found in source.")
                
    def _is_grounded(self, value: str, chunks: List[str]) -> bool:
        """Check if a single value is represented in any chunk."""
        # Simple exact substring check first (fast)
        value_lower = value.lower()
        for chunk in chunks:
            if value_lower in chunk.lower():
                return True
                
        # Semantic check (slower)
        for chunk in chunks:
            try:
                score = compute_similarity(value, chunk)
                if score >= self.threshold:
                    return True
            except Exception as e:
                logger.warning(f"Similarity check failed: {e}")
                # Fallback to fuzzy match or skip
                continue
                
        return False
