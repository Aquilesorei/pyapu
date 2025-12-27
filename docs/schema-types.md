# Schema Types

Define your expected output structure using strutex's schema types.

---

## Basic Types

### String

```python
from strutex import String

# Standard
name = String(description="Customer name")

# Simplified (if no args needed)
middle_name = String  # equivalent to String()
```

### Number

For floating-point values:

```python
from strutex import Number

price = Number  # equivalent to Number()
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

## Specialized Types

### Enum

Restrict output to a specific set of strings.

```python
from strutex import Enum

category = Enum(
    values=["Food", "Transport", "Lodging"],
    description="Expense category"
)
```

### Date

Extracts a string formatted as `YYYY-MM-DD`.

```python
from strutex import Date

invoice_date = Date(description="Invoice date")
```

### DateTime

Extracts a string formatted as ISO 8601 (`YYYY-MM-DDTHH:MM:SS`).

```python
from strutex import DateTime

created_at = DateTime(description="Metadata creation time")
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
    }
)
```

---

## JSON Schema Serialization

You can convert any schema object into a standard JSON Schema dictionary, useful for debugging or integrating with other tools.

```python
from strutex import String, Object
import json

schema = Object(
    properties={"name": String(description="User name")},
    required=["name"]
)

# Convert to dict
print(schema.to_dict())
# {
#     "type": "object",
#     "properties": {"name": {"type": "string", "description": "User name"}},
#     "required": ["name"],
#     "additionalProperties": False
# }

# Convert to JSON string
print(str(schema))
```
