# strutex

> **Stru**ctured **T**ext **Ex**traction — Extract structured JSON from documents using LLMs

[![CI](https://github.com/Aquilesorei/strutex/actions/workflows/ci.yml/badge.svg)](https://github.com/Aquilesorei/strutex/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/strutex.svg)](https://pypi.org/project/strutex/)

```bash
pip install strutex
```

---

## The Simplest Example

```python
from strutex import extract
from strutex.schemas import INVOICE_US

invoice = extract("invoice.pdf", model=INVOICE_US)
print(invoice.invoice_number, invoice.total)
```

**That's it.** Three lines. No custom schema to write.

> **Schemas are required** — but you have options:
>
> - **Built-in schemas** — 10+ ready-to-use (invoices, receipts, shipping docs, resumes)
> - **Native types** — `Object`, `String`, `Number`, `Array` (lightweight, no dependencies)
> - **Pydantic models** — Full type safety and validation

---

## What You Can Do

| Level             | Features                  | When to use                        |
| ----------------- | ------------------------- | ---------------------------------- |
| **Basic**         | `extract()`, schemas      | Most use cases — just extract data |
| **Reliability**   | `verify=True`, validators | Production — ensure accuracy       |
| **Scale**         | caching, async, batch     | High volume — reduce costs         |
| **Extensibility** | plugins, hooks, CLI       | Advanced — extend anything         |

> **Most users only need Level 1.** The rest is there when you need it.

---

## Level 1: Basic Extraction

### With Pydantic (recommended)

```python
import strutex
from pydantic import BaseModel

class Receipt(BaseModel):
    store: str
    date: str
    total: float

receipt = strutex.extract("receipt.jpg", model=Receipt)
```

### With Native Schema

```python
from strutex import extract, Object, String, Number

schema = Object(properties={
    "invoice_number": String,
    "total": Number,
})

result = extract("invoice.pdf", schema=schema)
```

### With Built-in Schemas

```python
from strutex import extract
from strutex.schemas import INVOICE_US, BILL_OF_LADING

invoice = extract("invoice.pdf", model=INVOICE_US)
bol = extract("bl.pdf", model=BILL_OF_LADING)
```

Available: `INVOICE_GENERIC`, `INVOICE_US`, `INVOICE_EU`, `RECEIPT`, `PURCHASE_ORDER`, `BILL_OF_LADING`, `RESUME`, `BANK_STATEMENT`, etc.

---

## Level 2: Reliability Features

### Optional Double-Check

Ask the LLM to validate its own answers automatically — adds accuracy, completely optional:

```python
result = strutex.extract(
    "contract.pdf",
    model=ContractSchema,
    verify=True  # LLM reviews its own output
)
```

### Choosing a Provider

Create a provider instance for full control over API keys and configuration:

```python
from strutex import DocumentProcessor
from strutex import GeminiProvider, OpenAIProvider, AnthropicProvider, OllamaProvider
from strutex.schemas import INVOICE_US
# Google Gemini
processor = DocumentProcessor(provider=GeminiProvider(api_key="your-key"))

# OpenAI
processor = DocumentProcessor(provider=OpenAIProvider(api_key="your-key", model="gpt-4o"))

# Anthropic Claude
processor = DocumentProcessor(provider=AnthropicProvider(api_key="your-key"))

# Local with Ollama (no API key needed)
processor = DocumentProcessor(provider=OllamaProvider(model="llama3"))

result = processor.process("doc.pdf", "Extract data", model=INVOICE_US)
```

> **Note:** String providers like `provider="gemini"` are convenience shortcuts that assume correct environment variables. For production, explicit provider instances are recommended.

---

## Level 3: Scale Features

### Caching (reduce API costs)

```python
from strutex import DocumentProcessor
from strutex.cache import SQLiteCache

processor = DocumentProcessor(
    provider="gemini",
    cache=SQLiteCache("cache.db")
)
```

### Async Processing

```python
import asyncio
from strutex import DocumentProcessor

async def main():
    processor = DocumentProcessor(provider="anthropic")
    results = await asyncio.gather(
        processor.aprocess("doc1.pdf", "Extract", schema),
        processor.aprocess("doc2.pdf", "Extract", schema)
    )

asyncio.run(main())
```

---

## Level 4: Extensibility

### Plugin System

Everything is pluggable. Just inherit from a base class:

| Type             | Purpose                 | Examples                          |
| ---------------- | ----------------------- | --------------------------------- |
| `Provider`       | LLM backends            | Gemini, OpenAI, Claude, Ollama    |
| `Extractor`      | Document parsing        | PDF, Image OCR, Excel             |
| `Validator`      | Output validation       | Schema, sum checks, date formats  |
| `SecurityPlugin` | Input/output protection | Injection detection, sanitization |
| `Postprocessor`  | Data transformation     | Date/number normalization         |

```python
from strutex.plugins import Provider, Extractor, Validator

# Custom LLM Provider
class MyProvider(Provider):
    """Auto-registered as 'myprovider'"""
    def process(self, file_path, prompt, schema, mime_type, **kwargs):
        # Call your LLM API
        ...

# Custom Document Extractor
class WordExtractor(Extractor, name="word"):
    """Handle .docx files"""
    mime_types = ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    def extract(self, file_path: str) -> str:
        # Parse .docx and return text
        ...

# Custom Validator
class TotalValidator(Validator):
    """Verify line items sum to total"""
    def validate(self, data, schema, context):
        items_sum = sum(item["amount"] for item in data.get("items", []))
        return ValidationResult(
            valid=abs(items_sum - data["total"]) < 0.01,
            message="Line items must sum to total"
        )
```

### CLI Commands

```bash
strutex plugins list              # List all plugins
strutex plugins list --type provider
strutex plugins info gemini --type provider
```

### For Distributable Packages

```toml
# pyproject.toml
[project.entry-points."strutex.providers"]
my_provider = "my_package:MyProvider"
```

### Hooks System

Inject logic at any point in the processing pipeline:

```python
from strutex import DocumentProcessor

processor = DocumentProcessor(provider="gemini")

@processor.on_pre_process
def add_instructions(file_path, prompt, schema, mime_type, context):
    """Modify prompt before sending to LLM"""
    return {"prompt": prompt + "\nBe precise and thorough."}

@processor.on_post_process
def normalize_dates(result, context):
    """Transform output after extraction"""
    if "date" in result:
        result["date"] = parse_date(result["date"])
    return result

@processor.on_error
def handle_rate_limit(error, file_path, context):
    """Custom error handling"""
    if "rate limit" in str(error).lower():
        return {"error": "Rate limited, please retry"}
    return None  # Propagate other errors
```

---

## Optional Extras

```bash
pip install strutex[cli]          # CLI commands
pip install strutex[ocr]          # OCR support
pip install strutex[langchain]    # LangChain integration
pip install strutex[llamaindex]   # LlamaIndex integration
pip install strutex[all]          # Everything
```

---

## Supported Formats

| Format | Extensions              | Method                              |
| ------ | ----------------------- | ----------------------------------- |
| PDF    | `.pdf`                  | Text extraction with fallback chain |
| Images | `.png`, `.jpg`, `.tiff` | Direct vision or OCR                |
| Excel  | `.xlsx`, `.xls`         | Converted to structured text        |
| Text   | `.txt`, `.csv`          | Direct input                        |

---

## Full Feature List

<details>
<summary>Click to expand all features</summary>

- **Plugin System v2** — Auto-registration via inheritance, lazy loading, entry points
- **Hooks** — Callbacks and decorators for pre/post processing pipeline
- **CLI Tooling** — `strutex plugins list|info|refresh` commands
- **Multi-Provider LLM Support** — Gemini, OpenAI, Anthropic, Ollama, Groq, Langdock
- **Universal Document Support** — PDFs, images, Excel, and custom formats
- **Schema-Driven Extraction** — Define your output structure, get consistent JSON
- **Verification & Self-Correction** — Built-in audit loop for high accuracy
- **Security First** — Built-in input sanitization and output validation
- **Framework Integrations** — LangChain, LlamaIndex, Haystack compatibility
- **Caching** — Memory, SQLite, and file-based caching
- **Async & Batch** — Process multiple documents in parallel
- **Streaming** — Real-time extraction feedback

</details>

---

## Documentation

📚 **[Read the Docs](https://aquilesorei.github.io/strutex/latest/)**

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full development plan.

**Recent releases:**

- [x] v0.1.0 — Core functionality
- [x] v0.2.0 — Plugin registry + Security layer
- [x] v0.3.0 — Plugin System v2
- [x] v0.6.0 — Built-in Schemas & Logging
- [x] v0.7.0 — Providers & Retries
- [x] v0.8.0 — Async, Batch, Cache, Verification
- [x] v0.8.1 — Documentation & Coverage Fixes

---

## License

This project is licensed under the **GNU General Public License v3.0** — see [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Priority areas:

1. **New plugins** — Providers, extractors, validators
2. **Documentation** — Examples and tutorials
3. **Testing** — Expand test coverage
