# Providers

LLM providers handle the actual document processing via their respective APIs.

---

## Built-in Providers

strutex includes 6 production-ready providers:

| Provider            | Cost | Priority | Capabilities             | Env Variable                        |
| ------------------- | ---- | -------- | ------------------------ | ----------------------------------- |
| `GeminiProvider`    | 1.0  | 50       | vision                   | `GEMINI_API_KEY` / `GOOGLE_API_KEY` |
| `OpenAIProvider`    | 2.0  | 60       | vision, function_calling | `OPENAI_API_KEY`                    |
| `AnthropicProvider` | 1.5  | 55       | vision, large_context    | `ANTHROPIC_API_KEY`                 |
| `OllamaProvider`    | 0.0  | 40       | vision, local            | `OLLAMA_HOST`                       |
| `GroqProvider`      | 0.3  | 45       | fast, vision             | `GROQ_API_KEY`                      |
| `LangdockProvider`  | 1.0  | 55       | enterprise, multi_model  | `LANGDOCK_API_KEY`                  |

---

## GeminiProvider

Google's Gemini models (default provider).

```python
from strutex import DocumentProcessor, GeminiProvider

# String shortcut (uses GEMINI_API_KEY or GOOGLE_API_KEY env vars)
processor = DocumentProcessor(provider="gemini")

# Explicit instance (recommended for production)
provider = GeminiProvider(
    api_key="...",  # or set GEMINI_API_KEY / GOOGLE_API_KEY
    model="gemini-2.5-flash"
)
processor = DocumentProcessor(provider=provider)
```

> **Note:** String providers like `provider="gemini"` are convenience shortcuts for registered providers. They assume the correct environment variables are set. For production, explicit provider instances are recommended.

**Features:**

- Native PDF/image processing (vision)
- Structured JSON output
- Fast and cost-effective

---

## OpenAIProvider

OpenAI GPT-4o and GPT-4 Vision.

```python
from strutex import OpenAIProvider

provider = OpenAIProvider(
    api_key="...",  # or set OPENAI_API_KEY
    model="gpt-4o",
    base_url=None,  # Custom endpoint (Azure, proxy)
    timeout=120.0
)
```

**Features:**

- Vision (GPT-4o, GPT-4 Vision)
- JSON response format
- Function calling support
- Custom base URL for Azure/proxies

**Models:**

- `gpt-4o` (recommended)
- `gpt-4-turbo`
- `gpt-4-vision-preview`

---

## AnthropicProvider

Claude 3.5 Sonnet and Claude 3 Opus.

```python
from strutex import AnthropicProvider

provider = AnthropicProvider(
    api_key="...",  # or set ANTHROPIC_API_KEY
    model="claude-3-5-sonnet-20241022",
    timeout=120.0
)
```

**Features:**

- Vision support (Claude 3+)
- Large context window (100k+ tokens)
- Excellent at following instructions

**Models:**

- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`

---

## OllamaProvider

Local models via Ollama (free, air-gapped).

```python
from strutex import OllamaProvider

provider = OllamaProvider(
    host="http://localhost:11434",  # or set OLLAMA_HOST
    model="llama3.2-vision",
    timeout=120.0
)
```

**Features:**

- Free (no API costs)
- Air-gapped/offline support
- Vision with multimodal models
- Respects `OLLAMA_HOST` env var

**Models:**

- `llama3.2-vision` (recommended for vision)
- `llama3.2`
- `llava`
- `bakllava`

!!! tip "Local-first Development"
Use Ollama for development to avoid API costs, then switch to cloud providers for production.

---

## GroqProvider

Ultra-fast inference at low cost.

```python
from strutex import GroqProvider

provider = GroqProvider(
    api_key="...",  # or set GROQ_API_KEY
    model="llama-3.3-70b-versatile",
    timeout=60.0
)
```

**Features:**

- Extremely fast inference (100+ tokens/sec)
- Very low cost
- JSON mode support
- Vision with specific models

**Models:**

- `llama-3.3-70b-versatile` (recommended)
- `llama-3.2-90b-vision-preview` (vision)
- `llama-3.2-11b-vision-preview` (vision)
- `mixtral-8x7b-32768`

---

## LangdockProvider

Enterprise-grade access to multiple LLM models via a unified API.

```python
from strutex import LangdockProvider

provider = LangdockProvider(
    api_key="...",  # or set LANGDOCK_API_KEY
    model="gemini-2.5-flash",
    temperature=0.0
)
```

**Features:**

- Enterprise-grade API access
- Multiple model support (Gemini, GPT-4, Claude)
- Document upload with attachment handling
- Structured JSON output via inline assistant

**Models:**

- `gemini-2.5-flash` (recommended)
- `gemini-2.5-pro`
- `gpt-4o`
- `gpt-4-turbo`
- `claude-3-5-sonnet`
- `claude-3-opus`

!!! note "Enterprise Usage"
Langdock is ideal for enterprise environments where you need access to multiple LLM providers through a single API.

---

## Retry Configuration

All providers support retry with exponential backoff:

```python
from strutex.providers import RetryConfig, OpenAIProvider

retry = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0
)

provider = OpenAIProvider(retry_config=retry)
```

---

## Health Checks

Check if a provider is available:

```python
from strutex import GeminiProvider, OllamaProvider

# Check if package installed and API key set
print(f"Gemini: {GeminiProvider.health_check()}")
print(f"Ollama: {OllamaProvider.health_check()}")  # Checks if server running
```

---

## Custom Providers

Create your own provider:

```python
from strutex.providers import Provider

class MyProvider(Provider, name="myprovider"):
    """Custom provider implementation."""

    strutex_plugin_version = "1.0"
    priority = 50
    cost = 1.0
    capabilities = ["vision"]

    def __init__(self, api_key=None, model="default"):
        self.api_key = api_key
        self.model = model

    def process(self, file_path, prompt, schema, mime_type, **kwargs):
        # Your implementation here
        ...
        return {"extracted": "data"}

    @classmethod
    def health_check(cls):
        # Check if provider is ready
        return True
```

**Usage:**

```python
processor = DocumentProcessor(provider="myprovider")
```

---

## Provider Selection

Choose the right provider for your needs:

| Use Case                    | Recommended Provider                    |
| --------------------------- | --------------------------------------- |
| Development/Testing         | `OllamaProvider` (free)                 |
| Production (cost-sensitive) | `GroqProvider` or `GeminiProvider`      |
| Production (quality)        | `OpenAIProvider` or `AnthropicProvider` |
| Air-gapped environments     | `OllamaProvider`                        |
| Large documents             | `AnthropicProvider` (large context)     |
| Speed-critical              | `GroqProvider`                          |

---

## See Also

- [Provider Chains](provider-chains.md) - Automatic fallback
- [Caching](cache.md) - Reduce API costs
