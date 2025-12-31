# Postprocessors

Postprocessors are plugins that run **after** the LLM extraction but **before** validation. They are used to normalize, clean, or enrich the extracted data.

strutex includes several built-in postprocessors for common data cleaning tasks.

## Using Postprocessors

You can use postprocessors individually or chain them together.

```python
from strutex import DatePostprocessor, NumberPostprocessor, PostprocessorChain

# Individual usage
date_pp = DatePostprocessor()
data = date_pp.process({"invoice_date": "15.01.2024"})
# Result: {"invoice_date": "2024-01-15"}

# Chained usage
chain = PostprocessorChain([
    DatePostprocessor(),
    NumberPostprocessor(),
])
result = chain.process(raw_data)
```

## Built-in Postprocessors

### DatePostprocessor

Normalizes date fields to a standard ISO format (`YYYY-MM-DD`).

It automatically detects fields with "date" in their name, or you can specify a list of `date_fields`.

**Features:**

- **Dynamic Format Support**: Automatically recognizes dates using standard separators (`-`, `/`, `.`, space, `_`).
- **No-Separator Support**: parses compact formats like `20240115` or `15012024`.
- **Text Month Support**: parses formats like "January 15, 2024" or "15 Jan 2024".
- **Year Range Validation**: Ignores dates outside the specified year range (default 1900-2100).
- **Configurable Output**: Defaults to `%Y-%m-%d` but can be customized.

**Configuration:**

```python
from strutex import DatePostprocessor

pp = DatePostprocessor(
    date_fields=["dob", "start_date"],  # Optional: specific fields
    separators=["-", "/", "."],         # Optional: custom separators
    output_format="%Y-%m-%d",           # Optional: custom output format
    min_year=1900,                      # Optional: min year validation
    max_year=2100                       # Optional: max year validation
)
```

### NumberPostprocessor

Parses formatted number strings (e.g., currency, percentages) into float or int values.

It automatically detects fields like "total", "amount", "price", "cost", "sum", "qty".

**Features:**

- **Currency Handling**: Removes symbols like $, €, £, ¥.
- **Locale Awareness**: Handles US (`1,234.56`) and European (`1.234,56`) formats.
- **Negative Numbers**: Handles parentheses `(100)` -> `-100`.

**Configuration:**

```python
from strutex import NumberPostprocessor

# Default (US locale)
pp = NumberPostprocessor()

# European locale (dot as thousand separator, comma as decimal)
pp_eu = NumberPostprocessor(locale="de_DE")
pp_eu.process({"total": "1.234,56 €"})
# Result: {"total": 1234.56}
```

### CurrencyNormalizer

Converts monetary amounts to a base currency. Adds new fields with a suffix (e.g., `_usd`).

**Features:**

- **Live Rates**: Can fetch current exchange rates from a public API.
- **Static Rates**: Can use a provided dictionary of exchange rates.
- **Auto-Conversion**: Converts fields if a `currency` field is present in the data.

**Configuration:**

```python
from strutex import CurrencyNormalizer

# Using static rates
pp = CurrencyNormalizer(
    base_currency="USD",
    exchange_rates={"EUR": 1.10, "GBP": 1.27}
)
result = pp.process({"total": 100, "currency": "EUR"})
# Result: {"total": 100, "currency": "EUR", "total_usd": 110.0}

# Fetching live rates
pp_live = CurrencyNormalizer(
    base_currency="USD",
    fetch_rates=True
)
```

### PostprocessorChain

Executes a list of postprocessors in sequence.

```python
from strutex import PostprocessorChain, DatePostprocessor

chain = PostprocessorChain([
    DatePostprocessor(),
    # ... other postprocessors
])
```

## Creating Custom Postprocessors

You can create your own postprocessor by inheriting from `strutex.Postprocessor`.

```python
from typing import Dict, Any
from strutex import Postprocessor, register

@register
class MyCustomPostprocessor(Postprocessor, name="my_custom"):
    priority = 50

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Modify data in place or return new dict
        if "title" in data:
            data["title"] = data["title"].upper()
        return data
```
