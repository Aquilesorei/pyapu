# Pydantic Support

Use Pydantic models for type-safe document extraction with automatic validation.

---

## Quick Start

```python
from pydantic import BaseModel, Field
from strutex import DocumentProcessor

class Invoice(BaseModel):
    invoice_number: str = Field(description="Unique ID")
    total: float = Field(description="Total amount")

processor = DocumentProcessor(provider="gemini")
result = processor.process(
    "invoice.pdf",
    "Extract invoice data",
    model=Invoice  # Use model= instead of schema=
)

# result is a validated Invoice instance!
print(result.invoice_number)
print(result.total)
```

---

## Nested Models

```python
from typing import List, Optional

class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total: float

class Vendor(BaseModel):
    name: str
    address: Optional[str] = None

class Invoice(BaseModel):
    invoice_number: str
    date: str = Field(description="YYYY-MM-DD format")
    vendor: Vendor
    items: List[LineItem]
    subtotal: float
    tax: Optional[float] = None
    total: float
```

---

## Field Descriptions

Use `Field(description=...)` to guide the LLM:

```python
class Invoice(BaseModel):
    invoice_number: str = Field(
        description="The unique invoice identifier, e.g. INV-2024-001"
    )
    date: str = Field(
        description="Invoice date in YYYY-MM-DD format"
    )
    total: float = Field(
        description="Final payable amount including tax"
    )
```

---

## Manual Conversion

You can also convert Pydantic models to strutex schemas manually:

```python
from strutex import pydantic_to_schema, validate_with_pydantic

# Convert model to schema
schema = pydantic_to_schema(Invoice)

# Later, validate dict data
data = {"invoice_number": "INV-001", "total": 100.0}
invoice = validate_with_pydantic(data, Invoice)
```

---

## Validation Errors

Pydantic validation runs after LLM extraction:

```python
from pydantic import ValidationError

try:
    result = processor.process(file, prompt, model=Invoice)
except ValidationError as e:
    print(f"Output didn't match schema: {e}")
```
