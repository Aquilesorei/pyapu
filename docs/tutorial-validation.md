# Adding Validation

Learn to validate extracted data for accuracy and consistency.

---

## Why Validate?

LLMs can make mistakes:

- **Math errors** — totals don't add up
- **Date formatting** — inconsistent formats
- **Missing required fields** — schema not enforced
- **Hallucinations** — data invented from nothing

Validation catches these before they reach your application.

---

## Built-in Validators

### SchemaValidator (Always Active)

Validates that output matches your schema structure:

```python
from strutex import DocumentProcessor
from pydantic import BaseModel

class Invoice(BaseModel):
    invoice_number: str
    total: float

processor = DocumentProcessor(provider="gemini")
result = processor.process("invoice.pdf", "Extract", model=Invoice)
# Schema validation happens automatically
```

### SumValidator

Checks that line items add up to totals:

```python
from strutex import DocumentProcessor
from strutex.validators import ValidationChain, SchemaValidator, SumValidator

# Create validation chain
validators = ValidationChain([
    SchemaValidator(),
    SumValidator()  # Checks: sum(items.price) == total
])

# The SumValidator will flag if totals don't match
# useful for invoices, receipts, purchase orders
```

### DateValidator

Ensures dates are valid and consistent:

```python
from strutex.validators import DateValidator

validators = ValidationChain([
    SchemaValidator(),
    DateValidator()  # Checks date format validity
])
```

---

## Verification Loop (Self-Correction)

Let the LLM audit its own work:

```python
result = processor.process(
    file_path="invoice.pdf",
    prompt="Extract invoice",
    model=Invoice,
    verify=True  #  LLM reviews and corrects errors
)
```

**How it works:**

1. First pass: Extract data
2. Second pass: LLM reviews extraction against document
3. Returns corrected result if errors found

This catches ~30% more errors at 2x API cost.

---

## Custom Validation

Add your own business logic:

```python
from strutex import DocumentProcessor

def validate_invoice(result, context):
    errors = []

    # Check PO number format
    if not result.get("po_number", "").startswith("PO-"):
        errors.append("PO number must start with 'PO-'")

    # Check date is not in future
    from datetime import datetime
    if result.get("date"):
        inv_date = datetime.strptime(result["date"], "%Y-%m-%d")
        if inv_date > datetime.now():
            errors.append("Invoice date cannot be in the future")

    if errors:
        result["_validation_warnings"] = errors

    return result

# Register as post-process hook
processor = DocumentProcessor(
    provider="gemini",
    on_post_process=validate_invoice
)
```

---

## Validation Strategies

| Scenario              | Strategy                        |
| --------------------- | ------------------------------- |
| **Invoices/receipts** | `SumValidator` + `verify=True`  |
| **Dates matter**      | `DateValidator`                 |
| **Critical data**     | All validators + custom rules   |
| **High volume**       | `SchemaValidator` only (fast)   |
| **Compliance**        | Custom hooks for business rules |

---

## Error Handling

```python
from strutex.validators import ValidationChain, SchemaValidator, SumValidator

chain = ValidationChain([SchemaValidator(), SumValidator()])

# Validate manually
is_valid, errors = chain.validate(result, schema)

if not is_valid:
    print(f"Validation failed: {errors}")
    # Handle errors...
```

---

## Next Steps

| Want to...           | Go to...                        |
| -------------------- | ------------------------------- |
| Learn about caching  | [Caching](cache.md)             |
| Add security checks  | [Security Layer](security.md)   |
| Use in RAG pipelines | [Integrations](integrations.md) |
