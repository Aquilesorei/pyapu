# strutex

> **Stru**ctured **T**ext **Ex**traction — Extract structured JSON from documents using LLMs

[![CI](https://github.com/Aquilesorei/strutex/actions/workflows/ci.yml/badge.svg)](https://github.com/Aquilesorei/strutex/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/strutex.svg)](https://pypi.org/project/strutex/)
[![codecov](https://codecov.io/gh/Aquilesorei/strutex/branch/main/graph/badge.svg)](https://codecov.io/gh/Aquilesorei/strutex)

---

## Features

- **Plugin System v2** — Auto-registration via inheritance, lazy loading, entry points
- **Hooks** — Callbacks and decorators for pre/post processing pipeline
- **CLI Tooling** — `strutex plugins list|info|refresh` commands
- **Multi-Provider LLM Support** — Gemini, OpenAI, Anthropic, and custom endpoints
- **Universal Document Support** — PDFs, images, Excel, and custom formats
- **Schema-Driven Extraction** — Define your output structure, get consistent JSON
- **Verification & Self-Correction** — built-in audit loop for high accuracy
- **Security First** — Built-in input sanitization and output validation
- **Framework Integrations** — LangChain, LlamaIndex, Haystack compatibility

---

## When to Choose Strutex

**Good fit:**

- Document → JSON (invoices, receipts, forms, tables)
- Schema-validated output, not free-form LLM text
- Security by default (injection detection, PII redaction)
- Local/air-gapped (Ollama, custom endpoints)
- Lightweight deps, pluggable architecture
- Production-ready: caching, batch/async, verification
- LangChain/LlamaIndex integration for RAG pipelines

**Not a fit:**

- Complex multi-step agents or autonomous workflows
- Vector search / embedding pipelines (use with LlamaIndex instead)
- Full LLM orchestration framework → combine with LangChain

> **TL;DR**: strutex turns messy documents into trustworthy structured data. Use it standalone or plugged into your RAG stack.

---

## What's New 

- **Framework Integrations**: LangChain, LlamaIndex, Haystack, and Unstructured.io fallback
- **DocumentInput**: Unified handling for file paths and BytesIO (HTTP uploads)
- **Optional Extras**: Install only the integrations you need

---

## Quick Start

### Installation

View on PyPI: [https://pypi.org/project/strutex/](https://pypi.org/project/strutex/)

```bash
# Core only
pip install strutex

# With CLI commands
pip install strutex[cli]

# With OCR support
pip install strutex[ocr]

# Framework integrations
pip install strutex[langchain]     # LangChain
pip install strutex[llamaindex]    # LlamaIndex
pip install strutex[haystack]      # Haystack
pip install strutex[fallback]      # Unstructured.io

# Everything
pip install strutex[all]
```

### Basic Usage

```python
from strutex import DocumentProcessor, Object, String, Number, Array

# Define your output schema
invoice_schema = Object(
    description="Invoice data",
    properties={
        "invoice_number": String(description="The invoice ID"),
        "total": Number(),
        "items": Array(
            items=Object(
                properties={
                    "description": String(),
                    "amount": Number(),
                }
            )
        )
    }
)

# Process a document
processor = DocumentProcessor(provider="gemini")
result = processor.process(
    file_path="invoice.pdf",
    prompt="Extract the invoice details.",
    schema=invoice_schema
)

print(result["invoice_number"])  # "INV-2024-001"
print(result["total"])           # 1250.00
```

### Advanced Usage

#### 1. Caching

Save API costs by caching results. Smart hashing avoids re-processing identical files/prompts.

```python
from strutex.cache import SQLiteCache

# Persistent cache across runs
processor = DocumentProcessor(
    provider="openai",
    cache=SQLiteCache("strutex_cache.db")
)
```

#### 2. Async Processing

Process multiple documents in parallel.

```python
import asyncio

async def main():
    processor = DocumentProcessor(provider="anthropic")

    # Run in parallel
    results = await asyncio.gather(
        processor.aprocess("doc1.pdf", "Summary", schema),
        processor.aprocess("doc2.pdf", "Summary", schema)
    )

asyncio.run(main())
```

#### 3. Verification & Self-Correction

Enable the audit loop to have the LLM double-check its work.

```python
result = processor.process(
    "contract.pdf",
    prompt="Extract clauses",
    schema=contract_schema,
    verify=True  # triggers self-correction loop
)
```

---

## CLI Commands (v0.3.0+)

```bash
# List all plugins
strutex plugins list

# Filter by type
strutex plugins list --type provider

# Get plugin details
strutex plugins info gemini --type provider

# Refresh discovery cache
strutex plugins refresh
```

---

## Plugin System

**Everything is pluggable.** Just inherit from a base class:

```python
from strutex.plugins import Provider

class MyProvider(Provider):
    """Auto-registered as 'myprovider'"""
    capabilities = ["vision"]

    def process(self, file_path, prompt, schema, mime_type, **kwargs):
        # Your LLM logic
        ...

# Customize with class arguments
class FastProvider(Provider, name="fast"):
    """Registered as 'fast' with high priority"""
    priority = 90  # Class attribute
    cost = 0.5

    def process(self, ...): ...
```

### For Distributable Packages

Use entry points in `pyproject.toml`:

```toml
[project.entry-points."strutex.providers"]
my_provider = "my_package:MyProvider"
```

### Plugin Types

| Type            | Purpose                 | Examples                          |
| --------------- | ----------------------- | --------------------------------- |
| `provider`      | LLM backends            | Gemini, OpenAI, Claude, Ollama    |
| `security`      | Input/output protection | Injection detection, sanitization |
| `extractor`     | Document parsing        | PDF, Image OCR, Excel             |
| `validator`     | Output validation       | Schema, sum checks, date formats  |
| `postprocessor` | Data transformation     | Date/number normalization         |

---

## Supported Formats

| Format | Extensions              | Method                              |
| ------ | ----------------------- | ----------------------------------- |
| PDF    | `.pdf`                  | Text extraction with fallback chain |
| Images | `.png`, `.jpg`, `.tiff` | Direct vision or OCR                |
| Excel  | `.xlsx`, `.xls`         | Converted to structured text        |
| Text   | `.txt`, `.csv`          | Direct input                        |

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

## Documentation

📚 **[Read the Docs](https://aquilesorei.github.io/strutex/latest/)**

```bash
# Install docs dependencies
pip install mkdocs mkdocs-material mkdocstrings[python] mike

# Serve locally
mkdocs serve

# Build static site
mkdocs build

# Deploy with versioning
mike deploy 0.3.0 latest --push
```

---

## License

This project is licensed under the **GNU General Public License v3.0** — see [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Priority areas:

1. **New plugins** — Providers, extractors, validators
2. **Documentation** — Examples and tutorials
3. **Testing** — Expand test coverage
