# Hooks System

Extend the strutex processing pipeline without modifying core components.

!!! tip "New in v0.4.2"
**Callback and decorator hooks** — No pluggy knowledge required! Use simple callbacks or decorators directly on `DocumentProcessor`.

---

## Plugins vs Hooks

Before diving in, understand the distinction:

|              | Plugins (Provider, Validator, etc.)      | Hooks (pre_process, post_process)        |
| ------------ | ---------------------------------------- | ---------------------------------------- |
| **Role**     | **core components** — do the actual work | **Monitors** — observe without replacing |
| **Pattern**  | Strategy (replace engine)                | Observer (wrap engine)                   |
| **Quantity** | One at a time                            | Many simultaneously                      |
| **Use case** | "Use OpenAI instead of Gemini"           | "Log every request and add timestamps"   |

**Rule of thumb:**

- Changing **what** runs? → Plugin
- Observing **when** things run? → Hook

---

## Quick Start (Recommended)

=== "Callbacks"

    ```python
    from strutex import DocumentProcessor

    processor = DocumentProcessor(
        on_pre_process=lambda fp, prompt, schema, mime, ctx: {
            "prompt": prompt + "\nBe precise."
        },
        on_post_process=lambda result, ctx: {
            **result, "processed": True
        },
        on_error=lambda error, fp, ctx: {
            "status": "error", "message": str(error)
        }
    )
    ```

=== "Decorators"

    ```python
    from strutex import DocumentProcessor
    from datetime import datetime

    processor = DocumentProcessor()

    @processor.on_post_process
    def add_timestamp(result, context):
        result["processed_at"] = datetime.now().isoformat()
        return result

    @processor.on_pre_process
    def add_date_context(file_path, prompt, schema, mime_type, context):
        """Inject today's date into prompt."""
        import datetime
        today = datetime.date.today().isoformat()

        # Example: modify prompt
        new_prompt = f"{prompt}\nToday's date is {today}."

        # We can also modify schema if needed (advanced)
        # schema = Object(properties={"invoice_number": String, "total": Number})

        return {"prompt": new_prompt}



    @processor.on_error
    def handle_rate_limit(error, file_path, context):
        if "rate limit" in str(error).lower():
            return {"error": "Rate limited, please retry later"}
        return None  # Propagate other errors
    ```

---

## Hook Types

| Hook              | Called            | Receives                                          | Returns                     |
| ----------------- | ----------------- | ------------------------------------------------- | --------------------------- |
| `on_pre_process`  | Before processing | `(file_path, prompt, schema, mime_type, context)` | `{"prompt": ...}` or `None` |
| `on_post_process` | After processing  | `(result, context)`                               | Modified result or `None`   |
| `on_error`        | On exception      | `(error, file_path, context)`                     | Fallback result or `None`   |

---

## Callbacks vs Decorators

| Approach       | Best For                                        |
| -------------- | ----------------------------------------------- |
| **Callbacks**  | Quick, inline transformations; lambda functions |
| **Decorators** | Reusable, named functions; complex logic        |

You can use **both** together — they execute in order:

```python
processor = DocumentProcessor(
    on_post_process=lambda r, c: {**r, "via_callback": True}
)

@processor.on_post_process
def via_decorator(result, context):
    result["via_decorator"] = True
    return result

# Result will have both keys
```

---

## Complete Example

```python
from strutex import DocumentProcessor, Object, String, Number
from datetime import datetime
import time

processor = DocumentProcessor(provider="gemini")

@processor.on_pre_process
def start_timer(file_path, prompt, schema, mime_type, context):
    context["start_time"] = time.time()
    print(f"Processing: {file_path}")
    return None

@processor.on_post_process
def add_metadata(result, context):
    result["_processed_at"] = datetime.now().isoformat()
    result["_elapsed_seconds"] = time.time() - context["start_time"]
    return result

@processor.on_error
def fallback_handler(error, file_path, context):
    print(f"Error processing {file_path}: {error}")
    return {"error": str(error), "file": file_path}

schema = Object(properties={"invoice_number": String(), "total": Number()})
result = processor.process("invoice.pdf", "Extract invoice data", schema)
```

---

## Hook Execution Order

1. **Pre-process hooks** run in registration order
2. **Security validation** (input sanitization)
3. **Provider processing** (LLM extraction)
4. **Security validation** (output validation)
5. **Post-process hooks** run in registration order
6. **Pydantic validation** (if model was provided)

If an error occurs at step 3, **error hooks** run until one returns a fallback.

---

## Advanced: Pluggy Integration

Callback/decorator hooks are automatically integrated with pluggy. This means:

- Your callbacks work alongside global pluggy plugins
- Third-party packages can register hooks via entry points
- All hooks execute through the same pipeline

### Global Pluggy Hooks

For distributed plugins or complex scenarios:

```python
from strutex.plugins import hookimpl, register_hook_plugin

class MetricsPlugin:
    @hookimpl
    def pre_process(self, file_path, prompt, schema, mime_type, context):
        context["start_time"] = time.time()

    @hookimpl
    def post_process(self, result, context):
        elapsed = time.time() - context["start_time"]
        metrics.record("extraction_time", elapsed)

register_hook_plugin(MetricsPlugin())
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  processor.process() calls call_hook("post_process", ...)       │
│                              │                                   │
│                              ▼                                   │
│              pluggy.PluginManager.hook.post_process()           │
│                              │                                   │
│     ┌────────────────────────┼────────────────────────┐         │
│     ▼                        ▼                        ▼         │
│  Callback       Decorator       Global Pluggy                   │
│  Hooks          Hooks           Plugins                         │
│  (wrapped in    (wrapped in     (registered via                 │
│  _CallbackHook) _CallbackHook)  register_hook_plugin)           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Reference

::: strutex.plugins.hooks.register_hook_plugin
options:
show_root_heading: true

::: strutex.plugins.hooks.unregister_hook_plugin
options:
show_root_heading: true
