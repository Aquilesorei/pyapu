"""
Verification Example - Self-correction with verify=True

Demonstrates:
- Automatic verification (verify=True)
- Manual verification with processor.verify()
- Async verification
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex import DocumentProcessor, GeminiProvider
from strutex.schemas import INVOICE_US


def main():
    """Synchronous verification example."""
    print("--- Synchronous Verification ---")
    
    # Initialize processor with explicit provider
    processor = DocumentProcessor(
        provider=GeminiProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-3-flash-preview"
        )
    )
    
    # Get the order.pdf in this directory
    pdf_path = os.path.join(os.path.dirname(__file__), "order.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Sample PDF not found: {pdf_path}")
        return
    
    # 1. Automatic Verification
    # This runs the extraction, then immediately runs a second pass 
    # to audit and correct the result.
    print("Processing with verification...")
    result = processor.process(
        file_path=pdf_path,
        prompt="Extract invoice details",
        model=INVOICE_US,
        verify=True  #  Triggers self-correction
    )
    
    print(f"\nVerified Result:")
    print(f"  Invoice #: {result.invoice_number}")
    print(f"  Total: {result.total}")
    print(f"  Vendor: {result.vendor.name if result.vendor else 'N/A'}")


async def async_main():
    """Asynchronous verification example."""
    print("\n--- Asynchronous Verification ---")
    
    processor = DocumentProcessor(
        provider=GeminiProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-3-flash-preview"
        )
    )
    
    pdf_path = os.path.join(os.path.dirname(__file__), "order.pdf")
    
    # Async verification
    result = await processor.aprocess(
        file_path=pdf_path,
        prompt="Extract data",
        model=INVOICE_US,
        verify=True
    )
    print(f"Async Verified Result: {result.invoice_number}")


if __name__ == "__main__":
    try:
        main()
        asyncio.run(async_main())
    except Exception as e:
        print(f"Error: {e}")
