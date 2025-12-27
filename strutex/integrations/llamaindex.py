"""
LlamaIndex integration for Strutex.
Allows using Strutex as a document reader within the LlamaIndex ecosystem.
"""
import json
from typing import List, Optional, Any, Dict, Union
from pathlib import Path

try:
    from llama_index.core.readers.base import BaseReader
    from llama_index.core.schema import Document
except ImportError:
    try:
        # Fallback for older LlamaIndex versions
        from llama_index.readers.base import BaseReader
        from llama_index.schema import Document
    except ImportError:
        raise ImportError(
            "Could not import llama_index. "
            "Please install llama-index to use StrutexReader: pip install llama-index"
        )

from strutex.processor import DocumentProcessor
from strutex.plugins.base import Provider
from strutex.types import Schema


class StrutexReader(BaseReader):
    """
    A LlamaIndex-compatible reader that uses Strutex to extract structured data
    from documents (PDF, Images, Excel) and returns them as LlamaIndex Documents.
    
    Example:
        reader = StrutexReader(schema=InvoiceSchema, provider="gemini")
        documents = reader.load_data(file_path="invoice.pdf")
    """

    def __init__(
        self,
        schema: Schema,
        provider: Union[str, Provider] = "gemini",
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the StrutexReader.

        Args:
            schema: The Pydantic model or schema class to validate extraction against.
            provider: The AI provider to use (e.g., 'gemini', 'openai').
            api_key: Optional API key for the provider.
            config: Extra configuration for the processor.
        """
        super().__init__()
        self.schema = schema
        self.processor = DocumentProcessor(
            provider=provider,
            api_key=api_key,
            **(config or {})
        )

    def load_data(
        self,
        file_path: Optional[str] = None,
        file: Optional[Path] = None,
        extra_info: Optional[Dict] = None
    ) -> List[Document]:
        """
        Load data from a file using Strutex extraction.

        Args:
            file_path: String path to the file.
            file: Path object to the file.
            extra_info: Additional metadata to include with the document.

        Returns:
            List containing a single LlamaIndex Document with structured data.
        """
        # Resolve file path
        path = str(file) if file else file_path
        if not path:
            raise ValueError("Must provide either file_path or file argument")
        
        # 1. Run the extraction using Strutex Core
        result = self.processor.process(
            file_path=path,
            schema=self.schema
        )

        # 2. Convert the Pydantic model (or dict) to a JSON string
        if hasattr(result, "model_dump"):
            data_dict = result.model_dump()
            content_str = result.model_dump_json(indent=2)
        else:
            data_dict = result if isinstance(result, dict) else {"data": str(result)}
            content_str = json.dumps(data_dict, indent=2)

        # 3. Build Metadata
        metadata = {
            "source": path,
            "extractor": "strutex",
            "provider": self.processor.provider_name,
            **(extra_info or {})
        }

        # Lift specific top-level fields to metadata for better filtering
        for key in ["date", "category", "type", "invoice_number", "vendor"]:
            if key in data_dict:
                metadata[key] = data_dict[key]

        # 4. Return as LlamaIndex Document
        return [Document(
            text=content_str,
            metadata=metadata
        )]


class StrutexNodeParser:
    """
    A simple node parser that keeps strutex-extracted documents as single nodes.
    
    Use this when you don't want LlamaIndex to split your structured JSON
    into multiple chunks (which would break the structure).
    
    Example:
        from strutex.integrations.llamaindex import StrutexReader, StrutexNodeParser
        
        reader = StrutexReader(schema=InvoiceSchema)
        docs = reader.load_data("invoice.pdf")
        
        parser = StrutexNodeParser()
        nodes = parser.get_nodes_from_documents(docs)
    """

    def get_nodes_from_documents(self, documents: List[Document]) -> List[Document]:
        """
        Return documents as-is without chunking.
        
        Strutex documents are already structured and should not be split.
        """
        return documents
