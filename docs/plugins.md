# Plugin System

Everything in pyapu is pluggable. Use defaults or register your own implementations.

!!! note "New in v0.3.0"
Plugin System v2 introduces auto-registration via inheritance, lazy loading, entry points, priority-based ordering, and CLI tooling.

---

## Plugin Types

| Type            | Purpose                 | Built-in Examples                       |
| --------------- | ----------------------- | --------------------------------------- |
| `provider`      | LLM backends            | Gemini, OpenAI                          |
| `security`      | Input/output protection | InputSanitizer, PromptInjectionDetector |
| `extractor`     | Document parsing        | PDF, Image, Excel                       |
| `validator`     | Output validation       | Schema, business rules                  |
| `postprocessor` | Data transformation     | DateNormalizer                          |

The `PluginType` enum provides type-safe access to these types:

```python
from pyapu.plugins import PluginType

PluginType.PROVIDER      # "provider"
PluginType.EXTRACTOR     # "extractor"
PluginType.VALIDATOR     # "validator"
PluginType.POSTPROCESSOR # "postprocessor"
PluginType.SECURITY      # "security"
```

---

## Quick Start

### Auto-Registration via Inheritance

Simply inherit from a base class and your plugin is automatically registered:

```python
from pyapu.plugins import Provider

class MyProvider(Provider):
    """Auto-registered as 'myprovider'"""
    capabilities = ["vision"]

    def process(self, file_path, prompt, schema, mime_type, **kwargs):
        return {"result": "data"}
```

That's it! No decorators or manual registration needed.

### Customizing Registration

Use class arguments to customize the name:

```python
class FastProvider(Provider, name="fast"):
    """Registered as 'fast' with high priority"""
    priority = 90  # Priority is a class attribute
    cost = 0.5
    capabilities = ["vision", "batch"]

    def process(self, *args, **kwargs):
        ...
```

### Opting Out of Auto-Registration

For intermediate base classes:

```python
class BasePdfProvider(Provider, register=False):
    """NOT registered - abstract base class"""
    def common_pdf_logic(self):
        ...

class AdobeProvider(BasePdfProvider):
    """Registered as 'adobeprovider'"""
    def process(self, *args, **kwargs):
        ...
```

!!! tip
Classes with unimplemented `@abstractmethod`s are automatically skipped - no need for `register=False`.

---

## Plugin Attributes

| Attribute              | Type    | Default | Description                                    |
| ---------------------- | ------- | ------- | ---------------------------------------------- |
| `pyapu_plugin_version` | `str`   | `"1.0"` | API version for compatibility                  |
| `priority`             | `int`   | `50`    | Order in waterfall (0-100, higher = preferred) |
| `cost`                 | `float` | `1.0`   | Cost hint (lower = cheaper)                    |
| `capabilities`         | `list`  | `[]`    | Features this plugin supports                  |

---

## Registration Methods

### 1. Auto-Registration (Recommended)

Just inherit from a base class:

```python
class MyProvider(Provider):
    def process(self, ...): ...
# → Registered as "myprovider"

class MyProvider(Provider, name="custom"):
    def process(self, ...): ...
# → Registered as "custom"
```

### 2. Entry Points (For Packages)

For distributable packages, register in `pyproject.toml`:

```toml title="pyproject.toml"
[project.entry-points."pyapu.providers"]
my_provider = "my_package:MyProvider"

[project.entry-points."pyapu.validators"]
my_validator = "my_package:MyValidator"
```

Plugins are **lazy loaded** — only imported when first used.

### 3. Decorator (For Aliases)

Use decorators to register the same plugin under multiple names:

```python
from pyapu.plugins import register, Provider

@register("provider", name="fast_v1")
class FastProvider(Provider, name="fast"):
    def process(self, ...): ...

# Now accessible as BOTH "fast" AND "fast_v1"
```

### 4. Manual Registration

```python
from pyapu.plugins import PluginRegistry

PluginRegistry.register("provider", "my_provider", MyProvider)
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
