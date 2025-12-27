"""
Haystack integration for Strutex.
Allows using Strutex as a component in Haystack 2.x pipelines.
"""
import json
from pathlib import Path
from typing import List, Optional, Any, Dict, Union

try:
    from haystack import component, Document
except ImportError:
    raise ImportError(
        "Could not import haystack. "
        "Please install haystack-ai to use StrutexConverter: pip install haystack-ai"
    )

from strutex.processor import DocumentProcessor
from strutex.plugins.base import Provider
from strutex.types import Schema


@component
class StrutexConverter:
    """
    A Haystack 2.x component that converts files into Documents using Strutex
    for structured extraction.

    This component can be used in an indexing pipeline to transform files
    (PDF, Images) into structured Haystack Documents.

    Exposes a 'run' method that takes 'sources' (file paths) and returns 'documents'.
    """

    def __init__(
            self,
            schema: Schema,
            provider: Union[str, Provider] = "gemini",
            api_key: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the StrutexConverter.

        Args:
            schema: The Pydantic model or schema class to validate extraction against.
            provider: The AI provider to use.
            api_key: Optional API key.
            config: Extra configuration for the processor.
        """
        self.schema = schema
        self.processor = DocumentProcessor(
            provider=provider,
            api_key=api_key,
            **(config or {})
        )

    @component.output_types(documents=List[Document])
    def run(self, sources: List[Union[str, Path]], meta: Optional[Dict[str, Any]] = None):
        """
        Process a list of files and return Haystack Documents.

        Args:
            sources: List of file paths to process.
            meta: Global metadata to attach to all documents.
        """
        documents = []
        meta = meta or {}

        for source in sources:
            file_path = str(source)

            # 1. Process with Strutex
            try:
                result = self.processor.process(
                    file_path=file_path,
                    schema=self.schema
                )

                # 2. Serialize to JSON
                if hasattr(result, "model_dump"):
                    data_dict = result.model_dump()
                    content_str = result.model_dump_json(indent=2)
                else:
                    data_dict = result if isinstance(result, dict) else {"data": str(result)}
                    content_str = json.dumps(data_dict, indent=2)

                # 3. Create Metadata
                doc_metadata = {
                    "source": file_path,
                    "extractor": "strutex",
                    "provider": self.processor.provider_name,
                    **meta
                }

                # Lift key fields for filtering
                for key in ["date", "category", "type", "invoice_number"]:
                    if key in data_dict:
                        doc_metadata[key] = data_dict[key]

                # 4. Create Haystack Document
                documents.append(Document(content=content_str, meta=doc_metadata))

            except Exception as e:
                # In a pipeline, we might want to log errors but continue processing other files
                print(f"Error processing {file_path} with Strutex: {e}")
                # Optional: create an error document or skip
                continue

        return {"documents": documents}