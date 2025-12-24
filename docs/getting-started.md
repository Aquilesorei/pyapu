# Getting Started

## Installation

```bash
pip install strutex
```

### Optional Dependencies

=== "OCR Support"

    ```bash
    pip install strutex[ocr]
    ```

=== "All Features"

    ```bash
    pip install strutex[ocr] pydantic
    ```

---

## Basic Usage

### 1. Define Your Schema

```python
from strutex import Object, String, Number, Array

schema = Object(
    description="Invoice data",
    properties={
        "invoice_number": String(description="The invoice ID"),
        "date": String(description="Invoice date"),
        "total": Number(description="Total amount"),
        "items": Array(
            items=Object(
                properties={
                    "description": String(),
                    "amount": Number()
                }
            )
        )
    }
)
```

### 2. Create a Processor

```python
from strutex import DocumentProcessor

processor = DocumentProcessor(
    provider="gemini",
    model_name="gemini-2.5-flash"
    # api_key="..."  # Or set GOOGLE_API_KEY env var
)
```

### 3. Process a Document

```python
result = processor.process(
    file_path="invoice.pdf",
    prompt="Extract all invoice data.",
    schema=schema
)

print(f"Invoice: {result['invoice_number']}")
print(f"Total: ${result['total']}")
```

---

## Environment Variables

| Variable         | Description             |
| ---------------- | ----------------------- |
| `GOOGLE_API_KEY` | Google Gemini API key   |
| `OPENAI_API_KEY` | OpenAI API key (future) |

---

## Supported File Types

| Format | Extensions              | Notes                        |
| ------ | ----------------------- | ---------------------------- |
| PDF    | `.pdf`                  | Native support, OCR fallback |
| Images | `.png`, `.jpg`, `.tiff` | Vision-capable model         |
| Excel  | `.xlsx`, `.xls`         | Converted to text            |
| Text   | `.txt`, `.csv`          | Direct input                 |

---

## Next Steps

- [Schema Types](schema-types.md) — Learn all available types
- [Prompt Builder](prompt-builder.md) — Build structured prompts
- [Plugin System](plugins.md) — Extend with custom plugins
- [Security](security.md) — Add input/output protection
