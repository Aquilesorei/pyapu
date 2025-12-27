# Validators

Validate LLM output for correctness and data quality.

---

## Overview

Validators check extracted data against rules and can be composed into chains.

```python
from strutex import SchemaValidator, SumValidator, ValidationChain

chain = ValidationChain([
    SchemaValidator(),
    SumValidator(tolerance=0.01),
])

result = chain.validate(data, schema)
if not result.valid:
    print(result.issues)
```

---

## Built-in Validators

### SchemaValidator

Ensures output structure matches expected schema.

```python
from strutex import SchemaValidator, Object, String, Number, Array

schema = Object(properties={
    "invoice_number": String,
    "total": Number,
    "items": Array(items=Object(properties={
        "amount": Number
    }))
})

validator = SchemaValidator()
result = validator.validate(data, schema)
```

**Checks:**

- Required fields are present
- Field types match (string, number, boolean, array, object)
- Nested objects validated recursively (issues reported with full path, e.g., `items.0.amount`)

### SumValidator

Verifies line items sum to stated total.

```python
from strutex import SumValidator

validator = SumValidator(
    items_field="line_items",
    amount_field="price",
    total_field="grand_total",
    tolerance=0.01
)

result = validator.validate({
    "line_items": [{"price": 10.00}, {"price": 20.00}],
    "grand_total": 30.00
})
# result.valid == True
```

### DateValidator

Validates date formats and ranges.

```python
from strutex import DateValidator

validator = DateValidator(
    date_fields=["invoice_date", "due_date"],
    min_year=2020,
    max_year=2030
)

result = validator.validate({
    "invoice_date": "2024-01-15",
    "due_date": "2024-02-15"
})
```

**Accepted formats:** ISO, European (DD.MM.YYYY), US (MM/DD/YYYY)

---

## Validation Chains

Compose multiple validators:

```python
from strutex import ValidationChain, SchemaValidator, SumValidator, DateValidator

chain = ValidationChain([
    SchemaValidator(strict=True),
    SumValidator(tolerance=0.01),
    DateValidator(),
], strict=True)  # Stop on first failure

result = chain.validate(data, schema)

print(result.valid)   # True/False
print(result.issues)  # List of error messages
print(result.data)    # Possibly modified data
```

**Modes:**

- `strict=True` — Stop on first failure
- `strict=False` — Collect all issues

---

## Creating Custom Validators

```python
from strutex.plugins import Validator, ValidationResult

class EmailValidator(Validator, name="email"):
    priority = 50

    def validate(self, data, schema=None):
        issues = []
        email = data.get("email", "")

        if email and "@" not in email:
            issues.append(f"Invalid email: {email}")

        return ValidationResult(
            valid=len(issues) == 0,
            data=data,
            issues=issues
        )
```

---

## API Reference

::: strutex.validators.SchemaValidator
options:
show_root_heading: true

::: strutex.validators.SumValidator
options:
show_root_heading: true

::: strutex.validators.DateValidator
options:
show_root_heading: true

::: strutex.validators.ValidationChain
options:
show_root_heading: true
