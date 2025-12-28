# Getting Started

## The Simplest Way

```python
import strutex
from pydantic import BaseModel

class Invoice(BaseModel):
    invoice_number: str
    total: float

result = strutex.extract("invoice.pdf", model=Invoice)
print(result.invoice_number, result.total)
```

**That's it.** You're done. Everything below is optional.

---

## Installation

```bash
pip install strutex
```

### Optional Extras

```bash
pip install strutex[cli]          # CLI commands
pip install strutex[ocr]          # OCR support
pip install strutex[langchain]    # LangChain integration
pip install strutex[all]          # Everything
```

---

## More Control: DocumentProcessor

For more control over the extraction process:

```python
from strutex import DocumentProcessor
from pydantic import BaseModel

class Invoice(BaseModel):
    invoice_number: str
    date: str
    total: float

processor = DocumentProcessor(provider="gemini")

result = processor.process(
    file_path="invoice.pdf",
    prompt="Extract the invoice details.",
    model=Invoice
)

print(f"Invoice: {result.invoice_number}")
print(f"Total: ${result.total}")
```

---

## Using Native Schemas

If you prefer not to use Pydantic:

```python
from strutex import extract, Object, String, Number

schema = Object(properties={
    "invoice_number": String(description="The invoice ID"),
    "total": Number(description="Total amount")
})

result = extract("invoice.pdf", schema=schema)
print(result["invoice_number"])
```

---

## Choosing a Provider

```python
# Default: Gemini (uses GOOGLE_API_KEY env var)
result = strutex.extract("doc.pdf", model=Schema)

# OpenAI
result = strutex.extract("doc.pdf", model=Schema, provider="openai")

# Anthropic
result = strutex.extract("doc.pdf", model=Schema, provider="anthropic")

# Local with Ollama
result = strutex.extract("doc.pdf", model=Schema, provider="ollama")
```

---

## Environment Variables

| Variable            | Description           |
| ------------------- | --------------------- |
| `GOOGLE_API_KEY`    | Google Gemini API key |
| `OPENAI_API_KEY`    | OpenAI API key        |
| `ANTHROPIC_API_KEY` | Anthropic API key     |

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

- [Your First Schema](tutorial-schema.md) — Define custom schemas
- [Built-in Schemas](schemas.md) — Ready-to-use Invoice, Receipt, etc.
- [Verification](verification.md) — Self-correction for accuracy
- [Caching](tutorial-caching.md) — Reduce API costs
