# Strutex

**Stru**ctured **T**ext **Ex**traction — Extract structured JSON from documents using LLMs.

---

## The Simplest Example

```python
import strutex
from pydantic import BaseModel

class Invoice(BaseModel):
    invoice_number: str
    total: float

result = strutex.extract("invoice.pdf", model=Invoice)
print(result.invoice_number, result.total)
```

**That's it.** Everything else in strutex is optional.

---

## What You Can Do

| Level             | Features                 | When to use    |
| ----------------- | ------------------------ | -------------- |
| **Basic**         | `extract()`, schemas     | Most use cases |
| **Reliability**   | verification, validation | Production     |
| **Scale**         | caching, async, batch    | High volume    |
| **Extensibility** | plugins, hooks           | Custom needs   |

> **Most users only need Level 1.** The rest is there when you need it.

---

## Documentation Map

### 📚 Tutorial (Start Here)

Progressive learning path from basics to advanced:

| #   | Page                                           | Description                                    |
| --- | ---------------------------------------------- | ---------------------------------------------- |
| 1   | [Quickstart](tutorial-quickstart.md)           | First extraction in 5 minutes                  |
| 2   | [Your First Schema](tutorial-schema.md)        | Define custom schemas (Pydantic & native)      |
| 3   | [Switching Providers](tutorial-providers.md)   | Configure GeminiProvider, OpenAIProvider, etc. |
| 4   | [Adding Validation](tutorial-validation.md)    | Validators and verification loop               |
| 5   | [Caching](tutorial-caching.md)                 | MemoryCache, SQLiteCache, FileCache            |
| 6   | [Processing Hooks](tutorial-hooks.md)          | Pre/post processing hooks                      |
| 7   | [Input Sanitization](tutorial-security.md)     | Input cleaning, PII redaction                  |
| 8   | [Batch & Async](tutorial-batch.md)             | process_batch, aprocess                        |
| 9   | [Streaming](tutorial-streaming.md)             | Real-time extraction feedback                  |
| 10  | [Error Handling](tutorial-error-handling.md)   | Errors, retries, debugging                     |
| 11  | [File Uploads](tutorial-document-input.md)     | BytesIO, Flask, FastAPI                        |
| 12  | [Integrations](tutorial-integrations.md)       | LangChain, LlamaIndex (Experimental)           |
| 13  | [Custom Plugins](tutorial-custom-plugins.md)   | Create Provider, Extractor, SecurityPlugin     |
| 14  | [The 10 Processors](processor-architecture.md) | Deep dive into all extraction strategies       |
| 15  | [Use Cases](tutorial-use-cases.md)             | Invoice, Receipt, Resume examples              |
| 16  | [Prompt Engineering](tutorial-prompts.md)      | StructuredPrompt builder                       |

---

### 📖 User Guide

Reference documentation for core features:

| Section     | Pages                                                                                              |
| ----------- | -------------------------------------------------------------------------------------------------- |
| **Schemas** | [Schema Types](schema-types.md) · [Built-in Schemas](schemas.md) · [Pydantic Support](pydantic.md) |
| **Prompts** | [Prompt Builder](prompt-builder.md) · [Verification](verification.md)                              |
| **RAG**     | [Retrieval-Augmented Generation](rag.md)                                                           |

---

### ⚡ Providers

LLM provider configuration and optimization:

| Page                                  | Description                    |
| ------------------------------------- | ------------------------------ |
| [Overview](providers.md)              | All supported providers        |
| [Provider Chains](provider-chains.md) | Fallback and cost optimization |
| [Caching Reference](cache.md)         | Detailed cache API             |

---

### 🔌 Integrations

Use with popular AI frameworks:

| Page                            | Description                                   |
| ------------------------------- | --------------------------------------------- |
| [Integrations](integrations.md) | LangChain, LlamaIndex, Haystack, Unstructured |

---

### 🔧 Advanced

For power users and contributors:

| Page                                           | Description                                     |
| ---------------------------------------------- | ----------------------------------------------- |
| [The 10 Processors](processor-architecture.md) | All extraction strategies (standard & advanced) |
| [Plugins API](plugins.md)                      | Custom provider and extractor reference         |
| [Hooks System](hooks.md)                       | Lifecycle hooks and event system                |
| [CLI Reference](cli.md)                        | Advanced command-line usage                     |
| [API Reference](api-reference.md)              | Autogenerated package reference                 |
| [CLI Commands](cli.md)                         | Command-line interface                          |

---

### 🏗 Architecture

Internal design and extension points:

| Page                              | Description                  |
| --------------------------------- | ---------------------------- |
| [Extractors](extractors.md)       | PDF, Excel, Image extractors |
| [Validators](validators.md)       | Schema, Sum, Date validators |
| [Input Sanitization](security.md) | Sanitization API             |

---

### 📋 Reference

| Page                              | Description            |
| --------------------------------- | ---------------------- |
| [API Reference](api-reference.md) | Full API documentation |
| [Changelog](changelog.md)         | Version history        |

---

## Installation

```bash
pip install strutex

# With integrations
pip install strutex[langchain]
pip install strutex[rag]
pip install strutex[all]
```

[→ Getting Started](getting-started.md)
