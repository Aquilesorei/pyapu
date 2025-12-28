#!/usr/bin/env python3
"""
Basic strutex usage example.

Demonstrates:
- Schema definition with Object, String, Number, Array
- DocumentProcessor creation with explicit provider
- Processing a PDF to extract structured data
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex import DocumentProcessor, Object, String, Number, Array, Integer
from strutex import GeminiProvider


def main():
    # ===================
    # 1. Define the Schema
    # ===================
    schema = Object(
        description="Invoice data extraction",
        properties={
            "invoice_number": String(description="Unique invoice identifier"),
            "date": String(description="Invoice date"),
            "vendor_name": String(description="Vendor/supplier name"),
            "total": Number(description="Total amount"),
            "line_items": Array(
                description="List of line items",
                items=Object(
                    properties={
                        "description": String,
                        "quantity": Integer,
                        "unit_price": Number,
                        "total": Number
                    }
                )
            )
        }
    )
    
    # ===================
    # 2. Create the Processor
    # ===================
    # Use explicit provider instance for full control over API key
    processor = DocumentProcessor(
        provider=GeminiProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-3-flash-preview"
        )
    )
    
    # ===================
    # 3. Process a Document
    # ===================
    prompt = """
    Extract all invoice data from this document.
    Include the invoice number, date, vendor name, total amount,
    and all line items with their details.
    """
    
    # Use the sample PDF in this folder
    pdf_path = os.path.join(os.path.dirname(__file__), "order.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Sample PDF not found: {pdf_path}")
        print("Please provide a PDF file to process.")
        return
    
    try:
        result = processor.process(
            file_path=pdf_path,
            prompt=prompt,
            schema=schema
        )
        
        # ===================
        # 4. Use the Results
        # ===================
        print("=" * 50)
        print("EXTRACTION RESULTS")
        print("=" * 50)
        print(f"Invoice Number: {result.get('invoice_number', 'N/A')}")
        print(f"Date: {result.get('date', 'N/A')}")
        print(f"Vendor: {result.get('vendor_name', 'N/A')}")
        print(f"Total: ${result.get('total', 0):.2f}")
        
        print("\nLine Items:")
        for i, item in enumerate(result.get("line_items", []), 1):
            print(f"  {i}. {item.get('description', 'N/A')}")
            print(f"     Qty: {item.get('quantity')} x ${item.get('unit_price', 0):.2f} = ${item.get('total', 0):.2f}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
