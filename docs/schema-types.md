# Schema Types

Define your expected output structure using strutex's schema types.

---

## Basic Types

### String

```python
from strutex import String

name = String(description="Customer name")
optional_name = String(description="Middle name", nullable=True)
```

### Number

For floating-point values:

```python
from strutex import Number

price = Number(description="Item price")
```

### Integer

For whole numbers:

```python
from strutex import Integer

quantity = Integer(description="Item count")
```

### Boolean

```python
from strutex import Boolean

is_paid = Boolean(description="Payment status")
```

---

## Complex Types

### Array

```python
from strutex import Array, String, Object

# Array of strings
tags = Array(items=String(), description="Item tags")

# Array of objects
items = Array(
    items=Object(
        properties={
            "name": String(),
            "price": Number()
        }
    )
)
```

### Object

```python
from strutex import Object, String

address = Object(
    description="Shipping address",
    properties={
        "street": String(),
        "city": String(),
        "zip": String()
    }
)
```

---

## Required vs Optional

By default, **all properties are required**. To make fields optional:

=== "Explicit Required"

    ```python
    schema = Object(
        properties={
            "name": String(),
            "email": String()
        },
        required=["name"]  # Only name is required
    )
    ```

=== "Nullable Fields"

    ```python
    schema = Object(
        properties={
            "name": String(),
            "notes": String(nullable=True)
        }
    )
    ```

---

## Complete Example

```python
from strutex import Object, String, Number, Integer, Array, Boolean

invoice_schema = Object(
    description="Complete invoice",
    properties={
        "invoice_number": String(description="Unique ID"),
        "date": String(description="YYYY-MM-DD"),
        "vendor": Object(
            properties={
                "name": String(),
                "address": String(nullable=True)
            }
        ),
        "items": Array(
            items=Object(
                properties={
                    "description": String(),
                    "quantity": Integer(),
                    "price": Number()
                }
            )
        ),
        "total": Number(),
        "paid": Boolean()
    }
)
```
