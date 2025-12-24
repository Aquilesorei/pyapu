# Providers

LLM providers handle the actual document processing.

---

## Built-in Providers

### GeminiProvider

Google's Gemini models (default).

```python
from strutex import DocumentProcessor

processor = DocumentProcessor(
    provider="gemini",
    model_name="gemini-2.5-flash"
)
```

**Environment:** Set `GOOGLE_API_KEY` or pass `api_key=`.

---

## Custom Providers

Create your own provider:

```python
from strutex.plugins import Provider, register

@register("provider", name="ollama")
class OllamaProvider(Provider):
    """Local Ollama provider."""

    capabilities = ["local", "vision"]

    def __init__(self, api_key=None, model="llama3"):
        self.model = model
        self.base_url = "http://localhost:11434"

    def process(self, file_path, prompt, schema, mime_type, **kwargs):
        import requests

        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()

        # Call Ollama API
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                # ...
            }
        )

        return response.json()
```

**Usage:**

```python
processor = DocumentProcessor(provider="ollama")
```

---

## Provider Capabilities

Declare what your provider supports:

```python
class MyProvider(Provider):
    capabilities = ["vision", "batch", "async"]

    def has_capability(self, name):
        return name in self.capabilities
```

**Common capabilities:**

| Capability  | Description                  |
| ----------- | ---------------------------- |
| `vision`    | Can process images directly  |
| `batch`     | Supports batch processing    |
| `async`     | Has async implementation     |
| `streaming` | Supports streaming responses |

---

## Async Support

Override `aprocess` for async:

```python
class AsyncProvider(Provider):
    async def aprocess(self, file_path, prompt, schema, mime_type, **kwargs):
        async with aiohttp.ClientSession() as session:
            # Async API call
            ...
```
