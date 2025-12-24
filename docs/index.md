# Strutex

**Python AI PDF Utilities** — Extract structured JSON from documents using LLMs.

---

## Features

<div class="grid cards" markdown>

- :material-clock-fast:{ .lg .middle } **Quick Setup**

  Install with pip and extract data from PDFs in minutes.

  [:octicons-arrow-right-24: Getting Started](getting-started.md)

- :material-puzzle:{ .lg .middle } **Fully Pluggable**

  Every component is a plugin. Swap providers, add validators.

  [:octicons-arrow-right-24: Plugin System](plugins.md)

- :material-shield-check:{ .lg .middle } **Security Layer**

  Protect against prompt injection with built-in sanitizers.

  [:octicons-arrow-right-24: Security](security.md)

- :material-language-python:{ .lg .middle } **Pydantic Support**

  Use Pydantic models for type-safe extractions.

  [:octicons-arrow-right-24: Pydantic](pydantic.md)

</div>

---

## Quick Example

=== "With Schema"

    ```python
    from strutex import DocumentProcessor, Object, String, Number

    schema = Object(properties={
        "invoice_number": String(description="Invoice ID"),
        "total": Number(description="Total amount")
    })

    processor = DocumentProcessor(provider="gemini")
    result = processor.process("invoice.pdf", "Extract invoice data", schema)

    print(result["invoice_number"])  # "INV-2024-001"
    ```

=== "With Pydantic"

    ```python
    from pydantic import BaseModel
    from strutex import DocumentProcessor

    class Invoice(BaseModel):
        invoice_number: str
        total: float

    processor = DocumentProcessor(provider="gemini")
    result = processor.process("invoice.pdf", "Extract data", model=Invoice)

    # result is a validated Invoice instance!
    print(result.invoice_number)
    ```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DocumentProcessor                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Security │→ │ Extractor│→ │ Provider │→ │Validator │    │
│  │  Chain   │  │  Plugin  │  │  Plugin  │  │  Plugin  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│         ↓            ↓            ↓            ↓            │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Plugin Registry                        │    │
│  │   @register("provider") / @register("validator")  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature                | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| **Plugin System**      | Register custom providers, validators, postprocessors |
| **Security Layer**     | Input sanitization, prompt injection detection        |
| **Pydantic Support**   | Type-safe extractions with automatic validation       |
| **Structured Prompts** | Build organized prompts with the fluent API           |
| **Multi-Provider**     | Gemini, OpenAI, Anthropic (extensible)                |
