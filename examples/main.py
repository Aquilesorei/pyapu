import os

from dotenv import load_dotenv

from strutex.processor import DocumentProcessor
from strutex.types import Object, String, Number, Array

load_dotenv()

# 1. Define schema using the new Clean Syntax
order_schema = Object(
    description="Order confirmation data",
    # Logic: 'required' is automatically inferred as ["order_id", "total_amount", "items"]
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


processor = DocumentProcessor(
    provider="gemini",  # Use the registered entry point name
    model_name="gemini-2.5-flash",
    api_key= os.getenv('GEMINI_API_KEY')
)


try:
    result = processor.process(
        file_path="order.pdf",
        prompt="Extract the order details strictly according to the schema.",
        schema=order_schema
    )
    print(result)

    #  4. Output the Validated Data
    # The 'result' is now a standard Python dictionary
    print("--- Extraction Successful ---")
    print(f"Order ID: {result['order_id']}")
    print(f"Total Amount: {result['total_amount']}")

    print("\nLine Items:")
    for item in result.get('items', []):
        print(f"- {item['item_name']}: {item['price']}")

except FileNotFoundError:
    print("Error: The file 'order.pdf' was not found.")
except Exception as e:
    print(f"An error occurred during processing: {e}")

