# Error Handling

Handle errors gracefully with Strutex's comprehensive exception hierarchy.

---

## Exception Hierarchy

All Strutex errors inherit from `StrutexError`, enabling catch-all patterns:

```
StrutexError (base)
├── ProviderError          # LLM API failures
│   ├── RateLimitError     # 429 - retry after delay
│   ├── AuthenticationError # 401 - invalid API key
│   └── ModelNotFoundError  # 404 - model unavailable
├── ExtractionError        # Document processing failed
│   ├── DocumentParseError  # Can't read file
│   └── SchemaError         # Invalid schema definition
├── ValidationError        # Output validation failed
├── ConfigurationError     # Setup/config issues
│   └── PluginError         # Plugin loading failed
├── CacheError             # Cache operations failed
├── SecurityError          # Security check failed
│   └── InjectionDetectedError  # Prompt injection detected
└── TimeoutError           # Operation timed out
```

---

## Quick Start

```python
from strutex import (
    DocumentProcessor,
    StrutexError,
    ProviderError,
    RateLimitError,
    ValidationError,
    ExtractionError,
)
import time

processor = DocumentProcessor(provider="gemini")

try:
    result = processor.process("invoice.pdf", "Extract invoice", schema=MySchema)
except RateLimitError as e:
    # Handle rate limiting with retry
    print(f"Rate limited, wait {e.retry_after}s")
    time.sleep(e.retry_after or 60)
except ProviderError as e:
    # Check if error is retryable
    if e.retryable:
        print(f"Retryable error from {e.provider}: {e.message}")
    else:
        print(f"Permanent error: {e.message}")
except ValidationError as e:
    # Handle validation failures
    print(f"Validation failed: {e.issues}")
except ExtractionError as e:
    # Handle extraction failures
    print(f"Failed at stage {e.stage}: {e.message}")
except StrutexError as e:
    # Catch-all for any Strutex error
    print(f"Strutex error: {e.message}")
    print(f"Details: {e.details}")
```

---

## Error Hook for Global Handling

```python
from strutex import DocumentProcessor, GeminiProvider
import logging

def global_error_handler(error, file_path, context):
    """Handle all extraction errors."""
    logging.error(f"Extraction failed for {file_path}: {error}")

    # Option 1: Return fallback
    return {"extraction_failed": True, "error": str(error)}

    # Option 2: Re-raise (return None)
    # return None

processor = DocumentProcessor(
    provider=GeminiProvider(),
    on_error=global_error_handler
)
```

---

## Retry Strategies

### Simple Retry

```python
import time
from strutex import DocumentProcessor, GeminiProvider

def process_with_retry(processor, file_path, prompt, schema, max_retries=3):
    for attempt in range(max_retries):
        try:
            return processor.process(file_path, prompt, schema=schema)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt  # Exponential backoff
            print(f"Attempt {attempt + 1} failed, retrying in {wait}s...")
            time.sleep(wait)

processor = DocumentProcessor(provider=GeminiProvider())
result = process_with_retry(processor, "doc.pdf", "Extract", MySchema)
```

### Using RetryConfig

```python
from strutex import ProviderChain, RetryConfig
from strutex import GeminiProvider, OpenAIProvider

# Create chain with retry config
chain = ProviderChain(
    providers=[GeminiProvider(), OpenAIProvider()],
    retry_config=RetryConfig(
        max_retries=3,
        backoff_factor=2.0,
        retry_on=[ConnectionError, TimeoutError]
    )
)

processor = DocumentProcessor(provider=chain)
```

---

## Provider Fallback

Fall back to another provider on failure:

```python
from strutex import DocumentProcessor, ProviderChain
from strutex import GeminiProvider, OpenAIProvider, OllamaProvider

# Try providers in order
chain = ProviderChain([
    GeminiProvider(),      # Try first
    OpenAIProvider(),      # Fall back
    OllamaProvider(),      # Last resort (local)
])

processor = DocumentProcessor(provider=chain)

# Automatically tries next provider on failure
result = processor.process("doc.pdf", "Extract", schema=MySchema)
```

---

## Debugging Extraction Issues

### Enable Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("strutex").setLevel(logging.DEBUG)

processor = DocumentProcessor(provider=GeminiProvider())
result = processor.process("doc.pdf", "Extract", schema=MySchema)
# See detailed logs
```

### Inspect Raw Response

```python
# Add post-process hook to see raw result
@processor.on_post_process
def debug_result(result, context):
    print(f"Raw result: {result}")
    print(f"Context: {context}")
    return result
```

### Check Provider Health

```python
from strutex import GeminiProvider

provider = GeminiProvider()

if provider.health_check():
    print("Provider is healthy")
else:
    print("Provider unavailable")
```

---

## Common Issues & Solutions

| Issue                      | Solution                                 |
| -------------------------- | ---------------------------------------- |
| "API key not found"        | Set env var: `export GOOGLE_API_KEY=...` |
| "Rate limit exceeded"      | Add retry with backoff, use caching      |
| "Invalid JSON response"    | Check prompt, use verify=True            |
| "Schema validation failed" | Check field types, use Optional[]        |
| "File too large"           | Use chunking or switch to Claude         |
| "Extraction timeout"       | Increase timeout, use smaller model      |

---

## Validation Errors

Handle validation failures separately:

```python
from strutex.validators import ValidationChain, SchemaValidator, SumValidator

chain = ValidationChain([SchemaValidator(), SumValidator()])

result = processor.process("invoice.pdf", "Extract", schema=InvoiceSchema)

# Validate separately
is_valid, errors = chain.validate(result, InvoiceSchema)

if not is_valid:
    print(f"Validation errors: {errors}")
    # Handle: log, alert, request human review
```

---

## Error Recovery in Batches

```python
from strutex import DocumentProcessor, GeminiProvider

processor = DocumentProcessor(provider=GeminiProvider())
files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

results = []
errors = []

for file_path in files:
    try:
        result = processor.process(file_path, "Extract", schema=MySchema)
        results.append({"file": file_path, "data": result})
    except Exception as e:
        errors.append({"file": file_path, "error": str(e)})

print(f"Success: {len(results)}, Failed: {len(errors)}")

# Retry failed files with different provider
if errors:
    fallback = DocumentProcessor(provider=OpenAIProvider())
    for err in errors:
        try:
            result = fallback.process(err["file"], "Extract", schema=MySchema)
            results.append({"file": err["file"], "data": result})
        except:
            pass  # Truly failed
```

---

## Next Steps

| Want to...        | Go to...                                  |
| ----------------- | ----------------------------------------- |
| See real examples | [Use Cases](tutorial-use-cases.md)        |
| Optimize prompts  | [Prompt Engineering](tutorial-prompts.md) |
| Add caching       | [Caching](tutorial-caching.md)            |
