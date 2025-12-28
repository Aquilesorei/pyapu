"""
Receipt Extraction Example

Demonstrates extracting structured data from receipts and purchase records.
"""

from strutex import DocumentProcessor, Object, String, Number, Array


receipt_schema = Object(
    description="Receipt/purchase data",
    properties={
        "merchant": Object(properties={
            "name": String,
            "address": String,
            "phone": String,
        }),
        "transaction_date": String,
        "transaction_time": String,
        "receipt_number": String,
        "items": Array(
            items=Object(properties={
                "description": String,
                "quantity": Number,
                "unit_price": Number,
                "total": Number,
            })
        ),
        "subtotal": Number,
        "tax": Number,
        "tax_rate": Number,
        "discounts": Array(
            items=Object(properties={
                "description": String,
                "amount": Number,
            })
        ),
        "total": Number,
        "payment_method": String,
        "card_last_four": String,
        "cashier": String,
    }
)

receipt_prompt = """
Extract all information from this receipt.

Guidelines:
- Extract merchant details
- List all line items with prices
- Calculate and verify totals
- Note payment method used
- Capture any discounts or promotions
"""


def extract_receipt(file_path: str):
    # "gemini" is a shortcut for registered providers (uses GEMINI_API_KEY or GOOGLE_API_KEY env vars)
    # For explicit control, use: GeminiProvider(api_key="...", model="...")
    processor = DocumentProcessor(provider="gemini")
    return processor.process(file_path, receipt_prompt, receipt_schema)


if __name__ == "__main__":
    print("Receipt Extraction Example")
    print(f"Schema fields: {len(receipt_schema.properties)}")
