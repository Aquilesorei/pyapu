"""
Example: Using Strutex with LangChain and LlamaIndex Integrations

This example demonstrates how to use Strutex's framework integrations
for extraction in RAG pipelines.
"""
import os
from pydantic import BaseModel
from typing import List, Optional

# Define schema
class InvoiceItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    amount: float

class Invoice(BaseModel):
    invoice_number: str
    vendor_name: str
    date: str
    items: List[InvoiceItem]
    subtotal: float
    tax: Optional[float] = None
    total: float


def langchain_example():
    """Example using StrutexLoader with LangChain."""
    try:
        from strutex.integrations import StrutexLoader, StrutexOutputParser
    except ImportError:
        print("LangChain not installed. Run: pip install strutex[langchain]")
        return
    
    print("=== LangChain Integration ===\n")
    
    # 1. Using StrutexLoader for document extraction
    loader = StrutexLoader(
        file_path="sample_invoice.pdf",
        schema=Invoice,
        provider="gemini"  # or "openai", "anthropic", etc.
    )
    
    print("Loading document with StrutexLoader...")
    # documents = loader.load()  # Uncomment with real file
    # print(f"Extracted: {documents[0].page_content[:200]}...")
    
    # 2. Using StrutexOutputParser for LLM response validation
    parser = StrutexOutputParser(
        schema=Invoice,
        validators=["schema"]  # Use strutex validators
    )
    
    print("Format instructions for LLM:")
    print(parser.get_format_instructions()[:200] + "...")
    print()


def llamaindex_example():
    """Example using StrutexReader with LlamaIndex."""
    try:
        from strutex.integrations import StrutexReader, StrutexNodeParser
    except ImportError:
        print("LlamaIndex not installed. Run: pip install strutex[llamaindex]")
        return
    
    print("=== LlamaIndex Integration ===\n")
    
    # 1. Create reader with schema
    reader = StrutexReader(
        schema=Invoice,
        provider="gemini"
    )
    
    print("StrutexReader configured for Invoice schema")
    # documents = reader.load_data("invoice.pdf")  # Uncomment with real file
    
    # 2. Use node parser to prevent chunking
    parser = StrutexNodeParser()
    print("StrutexNodeParser ready (keeps structured docs as single nodes)")
    print()


def document_input_example():
    """Example using DocumentInput for BytesIO handling."""
    from strutex import DocumentInput, DocumentProcessor
    import io
    
    print("=== DocumentInput Example ===\n")
    
    # From file path
    doc = DocumentInput("/path/to/invoice.pdf")
    print(f"From file: {doc}")
    
    # From BytesIO (e.g., from HTTP upload)
    pdf_bytes = b"%PDF-1.4 fake content"
    doc = DocumentInput(io.BytesIO(pdf_bytes), filename="upload.pdf")
    print(f"From BytesIO: {doc}")
    
    # Get MIME type
    print(f"MIME type: {doc.get_mime_type()}")
    
    # Use with processor (context manager handles temp files)
    print("Using with processor:")
    print("  with doc.as_file_path() as path:")
    print("      result = processor.process(path, schema=MySchema)")
    print()


if __name__ == "__main__":
    print("Strutex Framework Integrations Example\n")
    print("=" * 50)
    print()
    
    document_input_example()
    langchain_example()
    llamaindex_example()
    
    print("=" * 50)
    print("Done! See docs/integrations.md for full documentation.")
