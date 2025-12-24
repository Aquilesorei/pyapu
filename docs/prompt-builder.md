# Prompt Builder

Build structured, organized prompts with the `StructuredPrompt` fluent API.

---

## Basic Usage

```python
from strutex import StructuredPrompt

prompt = (
    StructuredPrompt()
    .add_general_rule("Extract data exactly as shown")
    .add_field_rule("invoice_number", "Look for 'Invoice No'")
    .add_output_guideline("Return valid JSON only")
    .compile()
)
```

**Output:**

```text
You are a highly accurate AI Data Extraction Assistant.

### 1. General Principles
- Extract data exactly as shown

### 2. Field Rules

**invoice_number**:
- Look for 'Invoice No'

### 3. Output Format
- Return valid JSON only
```

---

## Multiple Rules

Use variadic arguments for cleaner code:

```python
prompt = (
    StructuredPrompt()
    .add_general_rule(
        "Extract all visible data exactly as shown",
        "Use null for missing values",
        "Dates must be in YYYY-MM-DD format",
        "Numbers use dot as decimal separator"
    )
    .compile()
)
```

---

## Critical Fields

Mark important fields as critical:

```python
prompt = (
    StructuredPrompt()
    .add_field_rule(
        "total",
        "Final payable amount",
        "Usually labeled 'Total' or 'Grand Total'",
        critical=True
    )
    .compile()
)
```

**Output:**

```text
**total**:
- **CRITICAL**: Final payable amount
- **CRITICAL**: Usually labeled 'Total' or 'Grand Total'
```

---

## Custom Persona

```python
prompt = StructuredPrompt(
    persona="You are an expert German invoice analyst."
)
```

---

## Complete Example

```python
from strutex import StructuredPrompt

prompt = (
    StructuredPrompt(
        persona="You are a precise invoice extraction specialist."
    )
    .add_general_rule(
        "Extract all data exactly as shown in the document",
        "Do not invent missing values - use null",
        "Ignore handwritten annotations"
    )
    .add_field_rule(
        "invoice_number",
        "Look for 'Invoice No', 'Invoice #', 'Inv-'",
        critical=True
    )
    .add_field_rule(
        "date",
        "Invoice date, convert to YYYY-MM-DD format"
    )
    .add_field_rule(
        "total",
        "Final amount including tax",
        "May be labeled 'Total', 'Amount Due', 'Grand Total'",
        critical=True
    )
    .add_output_guideline(
        "Return valid JSON only",
        "No markdown code blocks",
        "Match the provided schema exactly"
    )
    .compile()
)
```

---

## Using with Processor

```python
from strutex import DocumentProcessor, StructuredPrompt

prompt = (
    StructuredPrompt()
    .add_general_rule("Extract invoice data")
    .add_field_rule("total", "Total amount", critical=True)
    .compile()
)

processor = DocumentProcessor(provider="gemini")
result = processor.process("invoice.pdf", prompt, schema)
```
