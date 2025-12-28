"""
GLiNER Entity Extraction Example.

This example shows how to use GLiNER for fast, local entity extraction.
GLiNER is a zero-shot NER model - no training needed, just specify labels.

Use cases:
- Fast preprocessing before LLM refinement
- Reducing LLM API costs
- Fully offline entity extraction

Requirements:
    pip install strutex[gliner]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strutex.extractors import GlinerExtractor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "order.pdf")


def basic_extraction():
    """Extract entities using default labels."""
    
    extractor = GlinerExtractor()
    
    # Returns formatted text with extracted entities
    result = extractor.extract(PDF_PATH)
    print(result)
    
    return result


def custom_labels():
    """Extract domain-specific entities."""
    
    # Define labels specific to your documents
    extractor = GlinerExtractor(
        labels=[
            "invoice_number",
            "date", 
            "company",
            "total_amount",
            "product",
            "quantity",
            "unit_price",
        ],
        threshold=0.25  # Lower threshold = more entities
    )
    
    result = extractor.extract(PDF_PATH)
    print(result)
    
    return result


def structured_output():
    """Get entities as structured data (not formatted string)."""
    
    extractor = GlinerExtractor(
        labels=["date", "money", "company"]
    )
    
    # Returns dict: {label: [entities]}
    entities = extractor.extract_structured(PDF_PATH)
    
    print("Extracted Entities:")
    for label, items in entities.items():
        print(f"\n{label.upper()}:")
        for item in items:
            print(f"  - {item['text']} (confidence: {item['score']:.2f})")
    
    return entities


def hybrid_with_llm():
    """Use GLiNER for fast extraction, LLM for refinement."""
    from strutex import DocumentProcessor
    from strutex.providers import GeminiProvider
    from strutex.schemas import INVOICE_GENERIC
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Step 1: Fast local extraction with GLiNER
    extractor = GlinerExtractor(
        labels=["invoice_number", "date", "company", "amount", "product"]
    )
    pre_extracted = extractor.extract(PDF_PATH)
    
    print("=== GLiNER Pre-extraction ===")
    print(pre_extracted[:500])
    
    # Step 2: Use pre-extracted context to guide LLM
    processor = DocumentProcessor(
        provider=GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))
    )
    
    # The LLM gets pre-extracted entities as hints
    prompt = f"""
    Extract invoice details. Use these pre-extracted entities as hints:
    
    {pre_extracted}
    
    Verify and structure the data according to the schema.
    """
    
    result = processor.process(
        PDF_PATH,
        prompt,
        model=INVOICE_GENERIC
    )
    
    print("\n=== LLM Refined Result ===")
    print(f"Invoice: {result.invoice_number}")
    print(f"Date: {result.invoice_date}")
    print(f"Total: {result.total}")
    
    return result


def shipping_documents():
    """Example for shipping/logistics documents."""
    
    extractor = GlinerExtractor(
        labels=[
            "container_number",
            "vessel_name",
            "port",
            "date",
            "company",
            "weight",
            "bill_of_lading_number",
        ],
        threshold=0.3
    )
    
    # Would work on a Bill of Lading PDF
    # result = extractor.extract("bill_of_lading.pdf")
    
    print("Shipping document extractor ready.")
    print(f"Configured labels: {extractor.labels}")


if __name__ == "__main__":
    print("=" * 60)
    print("GLINER ENTITY EXTRACTION EXAMPLE")
    print("=" * 60)
    
    print("\n1. Basic Extraction with Default Labels:")
    print("-" * 40)
    
    try:
        basic_extraction()
    except ImportError as e:
        print(f"GLiNER not installed: {e}")
        print("Install with: pip install strutex[gliner]")
    except Exception as e:
        print(f"Error: {e}")
