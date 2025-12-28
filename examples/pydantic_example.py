#!/usr/bin/env python3
"""
Pydantic integration example.

Demonstrates:
- Using Pydantic BaseModel instead of manual schema
- Getting typed, validated results
- Nested Pydantic models
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import List, Optional
from pydantic import BaseModel, Field

from strutex import DocumentProcessor, GeminiProvider


# ===================
# 1. Define Pydantic Models
# ===================

class LineItem(BaseModel):
    """Individual line item from an invoice."""
    description: str = Field(description="Item description")
    quantity: int = Field(description="Quantity ordered")
    unit_price: float = Field(description="Price per unit")
    total: float = Field(description="Line total (qty * price)")


class Invoice(BaseModel):
    """Complete invoice data."""
    invoice_number: str = Field(description="Unique invoice ID")
    date: str = Field(description="Invoice date in YYYY-MM-DD format")
    vendor_name: str = Field(description="Name of the vendor/supplier")
    subtotal: float = Field(description="Subtotal before tax")
    tax: Optional[float] = Field(default=None, description="Tax amount if applicable")
    total: float = Field(description="Final total amount")
    items: List[LineItem] = Field(description="List of line items")


def main():
    # ===================
    # 2. Create Processor
    # ===================
    processor = DocumentProcessor(
        provider=GeminiProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-3-flash-preview"
        )
    )
    
    # ===================
    # 3. Process with Pydantic Model
    # ===================
    pdf_path = os.path.join(os.path.dirname(__file__), "order.pdf")
    
    if not os.path.exists(pdf_path):
        print("Sample PDF not found. Using demo mode.")
        demo_mode()
        return
    
    prompt = """
    Extract all invoice data from this document.
    Be precise with numbers and dates.
    """
    
    try:
        # Pass model= instead of schema=
        result = processor.process(
            file_path=pdf_path,
            prompt=prompt,
            model=Invoice  # <-- Pydantic model
        )
        
        # result is a validated Invoice instance!
        print(f"Type: {type(result)}")
        print(f"Invoice: {result.invoice_number}")
        print(f"Date: {result.date}")
        print(f"Vendor: {result.vendor_name}")
        print(f"Total: ${result.total:.2f}")
        
        print("\nItems:")
        for item in result.items:
            # item is a validated LineItem instance
            print(f"  - {item.description}: {item.quantity} x ${item.unit_price:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_mode():
    """Demonstrate schema conversion without API call."""
    from strutex import pydantic_to_schema, validate_with_pydantic
    
    print("=== Schema Conversion Demo ===\n")
    
    # Convert Pydantic model to strutex schema
    schema = pydantic_to_schema(Invoice)
    
    print(f"Schema type: {schema.type}")
    print(f"Properties: {list(schema.properties.keys())}")
    print(f"Required: {schema.required}")
    
    # Demonstrate validation
    print("\n=== Validation Demo ===\n")
    
    sample_data = {
        "invoice_number": "INV-2024-001",
        "date": "2024-01-15",
        "vendor_name": "Acme Corp",
        "subtotal": 100.00,
        "tax": 10.00,
        "total": 110.00,
        "items": [
            {"description": "Widget", "quantity": 2, "unit_price": 50.00, "total": 100.00}
        ]
    }
    
    invoice = validate_with_pydantic(sample_data, Invoice)
    print(f"Validated: {invoice.invoice_number}")
    print(f"First item: {invoice.items[0].description}")


if __name__ == "__main__":
    main()
