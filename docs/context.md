# Processing Context

Share state across multi-step document workflows with `ProcessingContext`.

---

## Quick Start

```python
from strutex import DocumentProcessor, ProcessingContext
from strutex.schemas import INVOICE_US, RECEIPT

processor = DocumentProcessor(provider="gemini")
ctx = ProcessingContext()

# First extraction
invoice = ctx.extract(processor, "invoice.pdf", "Extract invoice", INVOICE_US)

# Store state for use in next step
ctx.set("expected_total", invoice.total)

# Second extraction using stored state
receipt = ctx.extract(
    processor,
    "receipt.jpg",
    f"Verify receipt total matches {ctx.get('expected_total')}",
    RECEIPT
)

# Check results
print(f"Processed {len(ctx.history)} documents")
print(f"Total time: {ctx.total_duration_ms:.0f}ms")
```

---

## State Management

Store and retrieve values across extraction steps:

```python
ctx = ProcessingContext()

# Store values
ctx.set("vendor_id", "ACME-001")
ctx.set("items", ["item1", "item2"])

# Retrieve values
vendor = ctx.get("vendor_id")
items = ctx.get("items", default=[])

# Check if key exists
if ctx.has("vendor_id"):
    print("Vendor ID found")

# Update multiple values
ctx.update({
    "total": 1500.00,
    "currency": "USD"
})

# Get all state
state = ctx.state  # Returns copy
```

---

## Extraction History

Every extraction is recorded:

```python
# Perform extractions
ctx.extract(processor, "doc1.pdf", "Extract", schema1)
ctx.extract(processor, "doc2.pdf", "Extract", schema2)

# Access history
for step in ctx.history:
    print(f"Step {step.step_id}:")
    print(f"  File: {step.file_path}")
    print(f"  Provider: {step.provider}")
    print(f"  Duration: {step.duration_ms:.0f}ms")
    print(f"  Success: {step.result is not None}")
```

### ExtractionStep Fields

| Field         | Type  | Description                   |
| ------------- | ----- | ----------------------------- |
| `step_id`     | str   | Unique step identifier        |
| `file_path`   | str   | Document path                 |
| `prompt`      | str   | Extraction prompt (truncated) |
| `provider`    | str   | Provider class name           |
| `result`      | Any   | Extraction result (or None)   |
| `error`       | str   | Error message (or None)       |
| `duration_ms` | float | Processing time               |
| `timestamp`   | str   | ISO timestamp                 |

---

## Metrics

```python
# Aggregate metrics
print(f"Total duration: {ctx.total_duration_ms:.0f}ms")
print(f"Success count: {ctx.success_count}")
print(f"Error count: {ctx.error_count}")

# Get last result
last = ctx.last_result
print(f"Last result: {last}")

# Get all successful results
all_results = ctx.get_results()
```

---

## Step Listeners

Get notified after each extraction:

```python
def log_step(step):
    if step.error:
        print(f" {step.file_path} failed: {step.error}")
    else:
        print(f" {step.file_path} completed in {step.duration_ms:.0f}ms")

ctx = ProcessingContext()
ctx.on_step(log_step)

# Listener called after each extraction
ctx.extract(processor, "doc.pdf", "Extract", schema)
# Output:  doc.pdf completed in 2150ms
```

---

## Batch Processing

For processing multiple documents, use `BatchContext`:

```python
from strutex import BatchContext
import os

# Get list of files
pdf_files = [f for f in os.listdir(".") if f.endswith(".pdf")]

# Create batch context
ctx = BatchContext(total_documents=len(pdf_files))

for pdf in pdf_files:
    try:
        result = ctx.extract(processor, pdf, "Extract invoice", INVOICE_US)
        ctx.set(pdf, result.invoice_number)
    except Exception as e:
        print(f"Failed: {pdf}")

    # Progress tracking
    print(f"Progress: {ctx.progress}/{ctx.total_documents} ({ctx.progress_percent:.1f}%)")
    print(f"Success rate: {ctx.success_rate:.1f}%")
    print(f"Avg time: {ctx.average_duration_ms:.0f}ms")
    print(f"ETA: {ctx.estimated_remaining_ms / 1000:.0f}s")

# Final summary
print(f"\nCompleted: {ctx.success_count}/{ctx.total_documents}")
```

### BatchContext Properties

| Property                 | Description                |
| ------------------------ | -------------------------- |
| `progress`               | Documents processed so far |
| `progress_percent`       | Progress as percentage     |
| `success_rate`           | Success rate as percentage |
| `average_duration_ms`    | Average time per document  |
| `estimated_remaining_ms` | Estimated time remaining   |

---

## Async Support

```python
import asyncio

async def batch_extract():
    ctx = ProcessingContext()

    for pdf in pdf_files:
        result = await ctx.aextract(
            processor, pdf, "Extract", INVOICE_US
        )
        print(f"Extracted: {result.invoice_number}")

    return ctx.get_results()

results = asyncio.run(batch_extract())
```

---

## Serialization

Export context for logging/persistence:

```python
# Serialize to dict
data = ctx.to_dict()

# Contains:
# - context_id
# - metadata
# - state
# - history (list of steps)
# - created_at
# - total_duration_ms
# - success_count
# - error_count

import json
print(json.dumps(data, indent=2, default=str))
```

---

## Best Practices

1. **Use meaningful context IDs:**

   ```python
   ctx = ProcessingContext(context_id="invoice-batch-2024-01")
   ```

2. **Store intermediate results:**

   ```python
   ctx.set("step1_result", result1)
   # Use in later steps
   previous = ctx.get("step1_result")
   ```

3. **Add listeners for monitoring:**

   ```python
   ctx.on_step(lambda s: log_to_monitoring(s))
   ```

4. **Use BatchContext for multiple documents:**

   - Get progress tracking for free
   - Estimate completion time

5. **Export history for debugging:**
   ```python
   with open("context.json", "w") as f:
       json.dump(ctx.to_dict(), f, default=str)
   ```
