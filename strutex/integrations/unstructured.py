"""
Unstructured.io fallback integration for Strutex.
Provides a hybrid processor that falls back to traditional OCR/partitioning
when LLM-based extraction fails.
"""
import logging
from typing import Any, Dict, Optional, Union

try:
    from unstructured.partition.auto import partition
except ImportError:
    partition = None

from strutex.processor import DocumentProcessor
from strutex.plugins.base import Provider
from strutex.types import Schema

logger = logging.getLogger(__name__)


class UnstructuredFallbackProcessor:
    """
    A wrapper around DocumentProcessor that falls back to Unstructured.io
    if the primary AI extraction fails.

    This ensures 'Hybrid Reliability':
    1. Try smart extraction (Strutex)
    2. If fail, use robust mechanical extraction (Unstructured)
    """

    def __init__(
            self,
            schema: Optional[Schema] = None,
            provider: Union[str, Provider] = "gemini",
            api_key: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None
    ):
        self.processor = DocumentProcessor(
            provider=provider,
            api_key=api_key,
            **(config or {})
        )
        self.schema = schema

        if partition is None:
            logger.warning(
                "Unstructured is not installed. Fallback will not work. "
                "Install with: pip install unstructured"
            )

    def process(self, file_path: str, schema: Optional[Schema] = None, prompt: str = "") -> Any:
        """
        Attempt extraction with Strutex. If it fails, return Unstructured partition data.

        Returns:
            - Validated Schema Object (if Strutex succeeds)
            - Dict with "text" and "elements" (if fallback triggers)
        """
        target_schema = schema or self.schema

        try:
            # 1. Try Strutex (Primary)
            return self.processor.process(
                file_path=file_path,
                schema=target_schema,
                prompt=prompt
            )

        except Exception as e:
            # 2. Fallback to Unstructured (Secondary)
            if partition is None:
                raise e  # Cannot fall back if library missing

            logger.error(f"Strutex extraction failed: {e}. Falling back to Unstructured.")

            try:
                elements = partition(filename=file_path)
                text_content = "\n\n".join([str(el) for el in elements])

                # Return a generic fallback structure
                return {
                    "_fallback_triggered": True,
                    "_error": str(e),
                    "text_content": text_content,
                    # We can't fill specific schema fields blindly,
                    # so we return the raw text mapped to a generic field
                    "raw_elements": [str(el) for el in elements]
                }
            except Exception as fallback_error:
                # If even fallback fails, raise the original error
                raise RuntimeError(
                    f"Both Strutex and Unstructured fallback failed. "
                    f"Original error: {e}"
                ) from fallback_error