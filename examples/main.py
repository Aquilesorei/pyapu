"""
Main strutex usage example.

A simple example showing the core workflow with explicit provider configuration.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strutex import DocumentProcessor, GeminiProvider
from strutex import Object, String, Number, Array


# 1. Define schema using the clean syntax
order_schema = Object(
    description="Order confirmation data",
    properties={
        "order_id": String(description="The unique order ID"),
        "total_amount": Number,
        "items": Array(
            items=Object(
                properties={
                    "item_name": String,
                    "price": Number,
                }
            )
        )
    }
)


# 2. Create processor with explicit provider instance
processor = DocumentProcessor(
    provider=GeminiProvider(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-3-flash-preview"
    )
)


# 3. Process the document
pdf_path = os.path.join(os.path.dirname(__file__), "order.pdf")

if not os.path.exists(pdf_path):
    print(f"Sample PDF not found: {pdf_path}")
    exit(1)

try:
    result = processor.process(
        file_path=pdf_path,
        prompt="Extract the order details strictly according to the schema.",
        schema=order_schema
    )
    
    # 4. Output the extracted data
    print("=" * 50)
    print("EXTRACTION RESULTS")
    print("=" * 50)
    print(f"Order ID: {result.get('order_id', 'N/A')}")
    print(f"Total Amount: {result.get('total_amount', 0)}")

    print("\nLine Items:")
    for item in result.get('items', []):
        print(f"  - {item.get('item_name')}: {item.get('price')}")

except FileNotFoundError:
    print("Error: The file 'order.pdf' was not found.")
except Exception as e:
    print(f"An error occurred during processing: {e}")
