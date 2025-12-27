# Your First Schema

Learn to define custom schemas for your specific documents.

---

## Why Custom Schemas?

Built-in schemas like `INVOICE_US` are great for standard documents. But your documents might have:

- Custom fields (e.g., `reference_number`, `department_code`)
- Different structure (e.g., multiple addresses)
- Domain-specific data (e.g., medical codes, legal citations)

---

## Option 1: Pydantic Models (Recommended)

The cleanest way to define schemas:

```python
from pydantic import BaseModel
from typing import List, Optional
from strutex import DocumentProcessor

# Define your schema
class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total: float

class PurchaseOrder(BaseModel):
    po_number: str
    vendor: str
    ship_to: str
    order_date: str
    items: List[LineItem]
    subtotal: float
    tax: Optional[float] = None
    total: float

# Use it
processor = DocumentProcessor(provider="gemini")
result = processor.process(
    file_path="purchase_order.pdf",
    prompt="Extract all purchase order details",
    model=PurchaseOrder  # Note: 'model' not 'schema'
)

# Result is a validated Pydantic model
print(f"PO#: {result.po_number}")
for item in result.items:
    print(f"  - {item.description}: ${item.total}")
```

---

## Option 2: Schema Types (No Pydantic)

If you prefer not to use Pydantic:

```python
from strutex import DocumentProcessor, Object, String, Number, Array

# Define schema using strutex types
order_schema = Object(
    description="Purchase Order",
    properties={
        "po_number": String(description="Purchase order number"),
        "vendor": String(description="Vendor name"),
        "total": Number(description="Total amount"),
        "items": Array(
            items=Object(properties={
                "description": String,  # Simplified syntax!
                "quantity": Number,
                "unit_price": Number
            })
        )
    }
)

# Use it
result = processor.process(
    file_path="order.pdf",
    prompt="Extract purchase order",
    schema=order_schema  # Note: 'schema' not 'model'
)

# Result is a dict
print(result["po_number"])
```

---

## Schema Best Practices

| Do                                            | Don't                                |
| --------------------------------------------- | ------------------------------------ |
| Use descriptive field names                   | Use abbreviations (`amt` → `amount`) |
| Add `description` to complex fields           | Leave descriptions empty             |
| Use `Optional` for fields that may be missing | Require everything                   |
| Keep nesting shallow (3 levels max)           | Create deeply nested structures      |

---

## Field Types Reference

You can use types as classes (e.g., `String`) or instances (e.g., `String(description="...")`).

| Pydantic Type | Strutex Type       | Use For                    |
| ------------- | ------------------ | -------------------------- |
| `str`         | `String`           | Text, IDs, names           |
| `int`         | `Integer`          | Counts, quantities         |
| `float`       | `Number`           | Prices, percentages        |
| `bool`        | `Boolean`          | Yes/no fields              |
| `List[T]`     | `Array(items=T)`   | Line items, tags           |
| `Optional[T]` | `T(nullable=True)` | Fields that may be missing |

---

## Next Steps

| Want to...                  | Go to...                                     |
| --------------------------- | -------------------------------------------- |
| Try different LLM providers | [Switching Providers](tutorial-providers.md) |
| Add validation rules        | [Adding Validation](tutorial-validation.md)  |
| See real-world schemas      | [Built-in Schemas](schemas.md)               |
