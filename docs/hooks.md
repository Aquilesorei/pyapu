# Hooks System

Extend the strutex processing pipeline without modifying core code.

!!! note "New in v0.3.0"
Hooks are powered by [pluggy](https://pluggy.readthedocs.io/), the same framework used by pytest.

---

## Overview

Hooks let you:

- **Pre-process** — Modify inputs before sending to the LLM
- **Post-process** — Transform results after extraction
- **Error handling** — Recover from failures gracefully

```python
from strutex.plugins import hookimpl, register_hook_plugin

class MyPlugin:
    @hookimpl
    def pre_process(self, file_path, prompt, schema, mime_type, context):
        context["start_time"] = time.time()
        return None  # Don't modify inputs

    @hookimpl
    def post_process(self, result, context):
        result["_elapsed"] = time.time() - context["start_time"]
        return result

register_hook_plugin(MyPlugin())
```

---

## Available Hooks

### `pre_process`

Called before document processing begins.

```python
@hookimpl
def pre_process(
    self,
    file_path: str,
    prompt: str,
    schema: Any,
    mime_type: str,
    context: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Args:
        file_path: Path to the document
        prompt: Extraction prompt
        schema: Expected output schema
        mime_type: MIME type of the document
        context: Mutable dict for sharing state between hooks

    Returns:
        Dict with modified values to override, or None
    """
```

**Use cases:**

- Add timing/logging
- Modify prompts dynamically
- Inject context from external systems

### `post_process`

Called after extraction completes.

```python
@hookimpl
def post_process(
    self,
    result: Dict[str, Any],
    context: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Args:
        result: The extracted data
        context: Context dict from pre_process

    Returns:
        Modified result dict, or None to keep original
    """
```

**Use cases:**

- Transform/normalize data
- Add metadata
- Send to external systems

### `on_error`

Called when processing fails. First plugin to return a result wins.

```python
@hookimpl
def on_error(
    self,
    error: Exception,
    file_path: str,
    context: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Args:
        error: The exception that occurred
        file_path: Document that was being processed
        context: Context dict

    Returns:
        Fallback result, or None to propagate the error
    """
```

**Use cases:**

- Return cached results on rate limit
- Provide default values
- Log errors to monitoring

---

## Registering Hook Plugins

```python
from strutex.plugins import register_hook_plugin, unregister_hook_plugin

class CostTracker:
    def __init__(self):
        self.total_cost = 0.0

    @hookimpl
    def post_process(self, result, context):
        # Track API costs
        self.total_cost += context.get("api_cost", 0)
        return None

tracker = CostTracker()
register_hook_plugin(tracker)

# Later...
unregister_hook_plugin(tracker)
print(f"Total cost: ${tracker.total_cost:.2f}")
```

---

## Complete Example

```python
import time
from strutex import DocumentProcessor
from strutex.plugins import hookimpl, register_hook_plugin

class LoggingPlugin:
    """Log all document processing."""

    @hookimpl
    def pre_process(self, file_path, prompt, schema, mime_type, context):
        context["start"] = time.time()
        print(f"[LOG] Processing: {file_path}")
        return None

    @hookimpl
    def post_process(self, result, context):
        elapsed = time.time() - context["start"]
        print(f"[LOG] Completed in {elapsed:.2f}s")
        return None

    @hookimpl
    def on_error(self, error, file_path, context):
        print(f"[LOG] Error on {file_path}: {error}")
        return None  # Don't recover, just log

# Register globally
register_hook_plugin(LoggingPlugin())

# Now all DocumentProcessor calls will be logged
processor = DocumentProcessor(provider="gemini")
result = processor.process("invoice.pdf", "Extract data", schema)
```

---

## Hook Execution Order

1. All `pre_process` hooks run (order determined by plugin registration)
2. Document is processed by the provider
3. All `post_process` hooks run
4. If error occurs, `on_error` hooks run until one returns a result

---

## Registration Hooks

These hooks register plugins dynamically without entry points:

```python
@hookimpl
def register_providers(self) -> List[type]:
    """Return provider classes to register."""
    return [MyProvider, AnotherProvider]

@hookimpl
def register_validators(self) -> List[type]:
    return [MyValidator]

@hookimpl
def register_postprocessors(self) -> List[type]:
    return [MyPostprocessor]

@hookimpl
def register_security(self) -> List[type]:
    return [MySecurityPlugin]

@hookimpl
def register_extractors(self) -> List[type]:
    return [MyExtractor]
```

---

## Fallback When Pluggy Unavailable

If `pluggy` is not installed, hooks degrade gracefully:

```python
from strutex.plugins.hooks import PLUGGY_AVAILABLE

if PLUGGY_AVAILABLE:
    register_hook_plugin(MyPlugin())
else:
    print("Hooks not available, install pluggy")
```

---

## API Reference

::: strutex.plugins.hooks.register_hook_plugin
options:
show_root_heading: true

::: strutex.plugins.hooks.unregister_hook_plugin
options:
show_root_heading: true

::: strutex.plugins.hooks.call_hook
options:
show_root_heading: true
