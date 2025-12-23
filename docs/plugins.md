# Plugin System

Everything in pyapu is pluggable. Use defaults or register your own implementations.

!!! note "New in v0.3.0"
Plugin System v2 introduces lazy loading, entry points, priority-based ordering, and CLI tooling.

---

## Plugin Types

| Type            | Purpose                 | Built-in Examples                       |
| --------------- | ----------------------- | --------------------------------------- |
| `provider`      | LLM backends            | Gemini, OpenAI                          |
| `security`      | Input/output protection | InputSanitizer, PromptInjectionDetector |
| `extractor`     | Document parsing        | PDF, Image, Excel                       |
| `validator`     | Output validation       | Schema, business rules                  |
| `postprocessor` | Data transformation     | DateNormalizer                          |

---

## Quick Start

### Minimal Provider

```python
from pyapu.plugins import Provider

class MyProvider(Provider):
    """All attributes are inherited from base class!"""
    capabilities = ["vision"]

    def process(self, file_path, prompt, schema, mime_type, **kwargs):
        return {"result": "data"}
```

The base class provides sensible defaults:

- `pyapu_plugin_version = "1.0"` (inherited)
- `priority = 50` (inherited)
- `cost = 1.0` (inherited)
- `health_check()` (inherited)

Override only if you need custom values.

---

## Plugin Attributes (v0.3.0+)

| Attribute              | Type    | Default | Description                                    |
| ---------------------- | ------- | ------- | ---------------------------------------------- |
| `pyapu_plugin_version` | `str`   | `"1.0"` | API version for compatibility                  |
| `priority`             | `int`   | `50`    | Order in waterfall (0-100, higher = preferred) |
| `cost`                 | `float` | `1.0`   | Cost hint (lower = cheaper)                    |
| `capabilities`         | `list`  | `[]`    | Features this plugin supports                  |

### Example with Custom Priority

```python
class FastProvider(Provider):
    priority = 80      # Preferred over default
    cost = 0.5         # Cheaper option
    capabilities = ["vision", "batch"]

    def process(self, *args, **kwargs):
        ...
```

---

## Registration Methods

### Recommended: Entry Points

Register plugins in `pyproject.toml` for automatic discovery:

```toml title="pyproject.toml"
[project.entry-points."pyapu.providers"]
my_provider = "my_package:MyProvider"

[project.entry-points."pyapu.validators"]
my_validator = "my_package:MyValidator"
```

Plugins are **lazy loaded** — only imported when first used.

### Manual Registration

```python
from pyapu.plugins import PluginRegistry

PluginRegistry.register("provider", "my_provider", MyProvider)
```

### Decorator (Deprecated)

!!! warning "Deprecated in v0.3.0"
Use entry points instead. The decorator still works but emits a warning.

```python
@register("provider", name="my_provider")  # Deprecated
class MyProvider(Provider):
    ...
```

---

## CLI Commands

```bash
# List all plugins
pyapu plugins list

# Filter by type
pyapu plugins list --type provider

# JSON output
pyapu plugins list --json

# Plugin details
pyapu plugins info gemini --type provider

# Refresh discovery cache
pyapu plugins refresh
```

Example output:

```
PROVIDERS
----------------------------------------
  ✓ ● gemini               v1.0      priority: 50
       └─ capabilities: vision
```

---

## Lazy Loading

Plugins are discovered but not loaded until first use:

```python
from pyapu.plugins import PluginRegistry

PluginRegistry.discover()

# Check plugin exists (not loaded yet)
info = PluginRegistry.get_plugin_info("provider", "gemini")
print(info["loaded"])  # False

# Now load it
cls = PluginRegistry.get("provider", "gemini")

# Check again
info = PluginRegistry.get_plugin_info("provider", "gemini")
print(info["loaded"])  # True
```

---

## Creating Custom Plugins

### Custom Provider

```python
from pyapu.plugins import Provider

class OllamaProvider(Provider):
    # Optional overrides
    priority = 60
    capabilities = ["local", "vision"]

    def __init__(self, model="llama3"):
        self.model = model

    def process(self, file_path, prompt, schema, mime_type, **kwargs):
        # Your implementation
        ...

    @classmethod
    def health_check(cls) -> bool:
        """Optional: custom health check."""
        try:
            # Check if Ollama is running
            return True
        except:
            return False
```

### Custom Validator

```python
from pyapu.plugins import Validator, ValidationResult

class SumValidator(Validator):
    """Verify line items sum to total."""
    priority = 70  # Run before default validators

    def validate(self, data, schema=None):
        items_sum = sum(i.get("amount", 0) for i in data.get("items", []))
        total = data.get("total", 0)

        if abs(items_sum - total) > 0.01:
            return ValidationResult(
                valid=False,
                data=data,
                issues=[f"Sum mismatch: {items_sum} != {total}"]
            )
        return ValidationResult(valid=True, data=data)
```

### Custom Postprocessor

```python
from pyapu.plugins import Postprocessor
import re

class DateNormalizer(Postprocessor):
    """Convert DD.MM.YYYY to YYYY-MM-DD."""

    def process(self, data):
        result = data.copy()
        if "date" in result:
            match = re.match(r'(\d{2})\.(\d{2})\.(\d{4})', result["date"])
            if match:
                d, m, y = match.groups()
                result["date"] = f"{y}-{m}-{d}"
        return result
```

---

## Pluggy Hooks

Extend the processing pipeline with hooks:

```python
from pyapu.plugins import hookimpl, register_hook_plugin

class LoggingPlugin:
    @hookimpl
    def pyapu_pre_process(self, file_path, prompt, schema, mime_type, context):
        context["start_time"] = time.time()
        print(f"Processing: {file_path}")

    @hookimpl
    def pyapu_post_process(self, result, context):
        elapsed = time.time() - context["start_time"]
        print(f"Completed in {elapsed:.2f}s")

# Register the hook plugin
register_hook_plugin(LoggingPlugin())
```

Available hooks:

| Hook                 | When              | Purpose                |
| -------------------- | ----------------- | ---------------------- |
| `pyapu_pre_process`  | Before extraction | Modify inputs, logging |
| `pyapu_post_process` | After extraction  | Transform results      |
| `pyapu_on_error`     | On failure        | Error recovery         |

---

## API Reference

::: pyapu.plugins.PluginRegistry
options:
show_root_heading: true
members: - register - get - list - discover

::: pyapu.plugins.Provider
options:
show_root_heading: true
