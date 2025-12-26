[# Strutex Roadmap

> **Stru**ctured **T**ext **Ex**traction — Extract structured JSON from documents using LLMs

_Updated: December 26, 2025 — With strategic recommendations to compete with Unstructured.io, MinerU, LlamaParse_

---

## 🎯 Core Philosophy: Pluggable by Default

**Everything in strutex is pluggable.** The library provides sensible defaults that work out of the box, but users can register their own implementations for any component.

```python
from strutex import DocumentProcessor
from strutex.plugins import Provider

# Use defaults - works immediately
processor = DocumentProcessor(provider="gemini")

# Or plug in your own
class MyCustomProvider(Provider, name="custom"):
    def process(self, file, prompt, schema, **kwargs):
        ...
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          strutex Pipeline                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─── HOOKS (Observers) ───┐                                             │
│  │ • on_pre_process        │ ◄── Logging, timing, prompt mods           │
│  └─────────────────────────┘                                             │
│              │                                                           │
│              ▼                                                           │
│  ┌─── PLUGINS (Components) ─┐                                            │
│  │ • SecurityPlugin         │ ◄── Validates input                       │
│  │ • Extractor              │ ◄── PDF → text                            │
│  │ • Provider               │ ◄── LLM call                              │
│  │ • Validator              │ ◄── Validates output                      │
│  │ • Postprocessor          │ ◄── Transforms result                     │
│  └──────────────────────────┘                                            │
│              │                                                           │
│              ▼                                                           │
│  ┌─── HOOKS (Observers) ───┐                                             │
│  │ • on_post_process       │ ◄── Add metadata, notifications            │
│  │ • on_error              │ ◄── Fallbacks, alerting                    │
│  └─────────────────────────┘                                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Plugins** = Strategy Pattern (replace core components)  
**Hooks** = Observer Pattern (intercept without replacing)

---

## ✅ Completed Releases

### v0.1.0 — Core Functionality

- ✅ Google Gemini provider
- ✅ Custom schema definition system (`Schema`, `Object`, `String`, etc.)
- ✅ Provider-agnostic schema adapters
- ✅ PDF text extraction with waterfall fallback
- ✅ Excel/spreadsheet support
- ✅ MIME type detection
- ✅ StructuredPrompt builder

### v0.2.0 — Plugin System + Security

- ✅ Plugin registry with `@register` decorator
- ✅ Base plugin classes: `Provider`, `SecurityPlugin`, `Postprocessor`, `Validator`, `Extractor`
- ✅ Built-in security: `InputSanitizer`, `PromptInjectionDetector`, `OutputValidator`
- ✅ Composable `SecurityChain`
- ✅ Pydantic model support

### v0.3.0 — Plugin System v2

- ✅ Auto-registration via inheritance (no decorators needed)
- ✅ Entry point discovery (`strutex.providers`, `strutex.validators`, etc.)
- ✅ Lazy loading (plugins loaded on first use)
- ✅ Priority & cost declarations
- ✅ CLI tooling (`strutex plugins list|info|refresh`)
- ✅ Pluggy hook system integration
- ✅ API versioning (`strutex_plugin_version`)
- ✅ Sandboxed plugin probing
- ✅ Discovery caching

### v0.4.0 — Pydantic & Provider Polish

- ✅ Enhanced Pydantic support with `StrutexType`
- ✅ Provider instance passing
- ✅ Security per-request override

### v0.5.0 — User-Friendly Hooks

- ✅ Callback hooks via constructor (`on_pre_process`, `on_post_process`, `on_error`)
- ✅ Decorator hooks (`@processor.on_pre_process`, etc.)
- ✅ Callbacks integrated with pluggy system
- ✅ Comprehensive hooks documentation
- ✅ Versioned documentation with mike
- ✅ CLI `strutex run config.yaml` command
- ✅ OLLAMA_HOST environment variable support in docs

---

## 📋 Upcoming Releases

### v0.5.5 — Testing & Stability 🔥 **IMMEDIATE PRIORITY**

**Focus: Make it bulletproof so people trust it in production**

> ⚠️ **Do this BEFORE v0.6.0** — People won't adopt new features if the core crashes on real docs.

- [ ] 🔥 **Achieve 80%+ test coverage** (pytest + hypothesis for schema edge cases)
- [x] 🔥 **Async tests, error injection, validation failure cases**
  - [x] ✅ Async provider tests added (`tests/test_async.py`)
  - [x] ✅ Error injection tests added (`tests/test_error_injection.py`)
- [ ] **Public fixtures**: Include 20+ sample invoices/PDFs (public domain) in `tests/fixtures/`
- [x] **CI with coverage & badges** (GitHub Actions + Codecov integration)
- [ ] Fix any remaining plugin priority/race conditions
- [x] 🔥 **Proper logging module** (`strutex.logging` with configurable handlers, STRUTEX_LOG_LEVEL env var)
- [x] **mypy in CI** (added to workflow, non-blocking initially)
- [ ] Add retry, timeout, and rate-limit handling to all providers (not just Gemini)

---

### v0.6.0 — Extraction, Validation & Schemas

**Focus: Concrete plugin implementations + killer built-in schemas**

- [ ] **Extractor plugin implementations**
  - `PDFExtractor` — Wrap existing `pdf_to_text` as plugin
  - `ImageExtractor` — OCR extraction
  - `ExcelExtractor` — Spreadsheet to structured data
- [ ] **Validator plugin implementations**
  - `SchemaValidator`, `SumValidator`, `DateValidator`
  - Validation chain composition
- [ ] **Large document chunking**
  - `PageChunker`, `SemanticChunker`
  - Map-reduce strategy for long documents

#### 🔥 Built-in Schemas Module (High Impact!) ✅

> This alone will drive ⭐ stars — people want "plug and play" for invoices more than fancy architecture.

- [x] 🔥 **Ship `strutex.schemas` module** with 9 ready-to-use Pydantic schemas:
  - `INVOICE_US`, `INVOICE_EU`, `INVOICE_GENERIC`
  - `RECEIPT`, `PURCHASE_ORDER`, `BILL_OF_LADING`
  - `BANK_STATEMENT`, `CONTRACT_CLAUSE`, `RESUME`
- [x] Each schema importable in one line:
  ```python
  from strutex.schemas import INVOICE_US
  result = processor.process("invoice.pdf", schema=INVOICE_US)
  ```
- [x] Documentation at `docs/schemas.md`
- [ ] Example folder with full end-to-end demos for each schema type

---

### v0.7.0 — Multi-Provider & Context ✅

**Focus: Provider flexibility and stateful workflows**

- [x] **Additional providers** (with env var support and retry logic) ✅
  - [x] `OpenAIProvider` — GPT-4o, GPT-4 Vision
  - [x] `AnthropicProvider` — Claude 3.5 Sonnet
  - [x] `OllamaProvider` — Local models (respects `OLLAMA_HOST`)
  - [x] `GroqProvider` — Fast & cheap (llama-3.3-70b, vision models)
- [x] **Retry utilities** (`RetryConfig`, exponential backoff, `RateLimiter`)
- [x] 🔥 **Provider fallback chains** ✅
  - [x] `ProviderChain` — Automatic fallback between providers
  - [x] `local_first_chain()` — Ollama → Gemini → OpenAI
  - [x] `cost_optimized_chain()` — Ordered by cost
- [x] **ProcessingContext** ✅ — Share state across multi-step extractions
  - [x] `ProcessingContext` — History tracking, state management, listeners
  - [x] `BatchContext` — Progress tracking, success rates, time estimation
- [x] **Streaming response support** ✅
  - [x] `StreamingProcessor` — Wrapper for streaming extraction
  - [x] `StreamChunk` — Typed streaming chunks
  - [x] Utility functions (`stream_to_string`, `stream_with_callback`)

---

### v0.8.0 — Caching & Performance ✅

**Focus: Cost reduction and speed**

- [x] **Cache plugin system** ✅
  - [x] `MemoryCache` — LRU cache with TTL, thread-safe
  - [x] `SQLiteCache` — Persistent cache with automatic cleanup
  - [x] `FileCache` — Simple JSON file cache
  - [x] `CacheKey` — Smart hashing: `hash(file + prompt + schema + provider)`
- [x] **Async processing** — `async def aprocess()` (Implemented)
- [x] **Batch processing** — `process_batch` and `BatchContext` (Implemented)
- [x] **Token/cost tracking** — Usage metadata in ProcessingContext (Implemented)
- [x] 🔥 **Hybrid OCR fallback**: Traditional parsers (pdfplumber/Tesseract) when LLM not needed for speed/cost (Implemented `HybridProvider`)
- [x] **Verification Loop** — `process(verify=True)` for LLM-based self-correction (Implemented)

---

### v0.8.5 — Ecosystem Integrations 🔥

**Focus: Get adopted everywhere RAG is built**

> These integrations will get you forked/shared in every RAG tutorial.

- [ ] 🔥 **LlamaIndex integration**: `StrutexParser` node/loader
- [ ] 🔥 **LangChain integration**: `StrutexLoader` + `StrutexOutputParser`
- [ ] **Haystack compatibility**
- [ ] **Unstructured.io fallback**: Hybrid mode where you fall back to `unstructured.partition` if LLM fails
- [ ] 🔥 **Comparison table in docs** vs competitors (highlight local-first, security, validation)

---

### v0.9.0 — Postprocessing & Reliability

**Focus: Data transformation + hallucination detection**

- [ ] **Postprocessor plugins**
  - `DateNormalizer`, `NumberNormalizer`, `UomNormalizer`
  - Composable pipelines
- [ ] **Field targeting** — Apply transforms to specific fields
- [ ] **Currency conversion**
- [ ] 🔥 **Confidence scores per-field**
- [ ] 🔥 **Hallucination detection** (self-consistency checks, multi-model voting for critical fields)

---

### v1.0.0 — Production Ready 🚀

**Focus: Enterprise features and "it just works" experience**

- [ ] **Verification plugins**
  - `LLMVerifier` — Self-correction pass
  - `ReferenceVerifier` — Ground against reference data
- [ ] **Human-in-the-loop** — Review callbacks for low-confidence results
- [ ] **REST API server** — FastAPI wrapper
- [ ] **Docker image** — Pre-configured with OCR dependencies
- [ ] **Comprehensive CLI**
  - `strutex extract invoice.pdf --schema invoice_us --output json`
  - `strutex batch folder/*.pdf --output jsonl` with progress bars
  - `strutex serve` — Start REST API
  - 🔥 `strutex demo invoice.pdf` — One-command demo with local Ollama fallback

---

## 🔮 Future Considerations

- 🌐 **Document Classification** — Auto-detect document type before extraction
- 🧠 **Confidence Scores** — Per-field extraction confidence
- 📚 **Template Library** — Pre-built schemas for invoices, receipts, contracts
- 🎛️ **Web Dashboard** — Visual plugin configuration and monitoring
- 🔗 **Extraction Chains** — Multi-step workflows with dependencies
- 📊 **Evaluation Framework** — Benchmark extraction accuracy
- 🔥 **Public benchmark dataset** — 100+ tricky invoices with ground truth (monthly leaderboard vs competitors)

---

## 🚀 Visibility & Community Momentum

> Great code isn't enough — you need traction. Projects like MinerU (~50k ⭐) and Unstructured.io (~13k ⭐) exploded because they solve real pain instantly.

### Immediate (with v0.6.0 release)

- [ ] 🔥 **Build proper docs site** (MkDocs + Material theme) with quickstart <5 min
- [ ] Add PyPI badges: version, downloads, tests passing, coverage
- [ ] 🔥 **Post on**: r/Python, r/MachineLearning, r/LangChain
- [ ] **Show HN** at v1.0.0 launch

### Mid-Term

- [ ] Open "good first issues": "Add Groq provider", "Add schema for French invoices", "Improve table handling"
- [ ] CONTRIBUTING.md that's welcoming
- [ ] Discord/Slack for quick help — people love real-time chat for LLM tools
- [ ] Blog series: "Why strutex over wrappers?" + anonymized company case studies

### Long-Term Differentiation

- [ ] 🔥 **Stay local-first**: Best Ollama/Groq/HuggingFace support → own the air-gapped/cheap niche
- [ ] **Security emphasis**: Market PII redaction for compliance-heavy users (HIPAA, GDPR)
- [ ] Hybrid OCR fallback for speed/cost optimization
- [ ] Public benchmark dataset with monthly leaderboard

---

## Plugin Types Summary

| Plugin Type     | Base Class       | Purpose                 | Built-in Examples                 |
| --------------- | ---------------- | ----------------------- | --------------------------------- |
| `provider`      | `Provider`       | LLM backends            | Gemini, OpenAI, Anthropic, Ollama |
| `security`      | `SecurityPlugin` | Input/output protection | Sanitizer, InjectionDetector      |
| `extractor`     | `Extractor`      | Document parsing        | PDF, Image, Excel                 |
| `validator`     | `Validator`      | Output validation       | Schema, Sum, Date                 |
| `postprocessor` | `Postprocessor`  | Data transformation     | DateNormalizer, NumberNormalizer  |

---

## Version History

| Version | Status      | Focus                                     |
| ------- | ----------- | ----------------------------------------- |
| v0.1.0  | ✅ Released | Core functionality                        |
| v0.2.0  | ✅ Released | Plugin System + Security                  |
| v0.3.0  | ✅ Released | Plugin v2: Entry Points + Lazy Load       |
| v0.4.0  | ✅ Released | Pydantic & Provider Polish                |
| v0.5.0  | ✅ Released | User-Friendly Hooks                       |
| v0.5.5  | 🔥 Next     | Testing & Stability                       |
| v0.6.0  | 📋 Planned  | Extraction, Validation & Schemas          |
| v0.7.0  | 📋 Planned  | Multi-Provider & Context                  |
| v0.8.0  | ✅ Released | Caching & Performance                     |
| v0.8.1  | ✅ Released | Documentation & Coverage Fixes            |
| v0.8.5  | 📋 Planned  | Ecosystem Integrations (LlamaIndex, etc.) |
| v0.9.0  | 📋 Planned  | Postprocessing & Reliability              |
| v1.0.0  | 📋 Planned  | Production Ready (API, Docker, CLI)       |

---

## 🎯 Priority Summary (Next 1-2 Months)

Execute these 🔥 items first to hit traction inflection point:

1. **v0.5.5 Stability** — 80%+ coverage, proper logging, mypy strict
2. **v0.6.0 Schemas** — 15-20 built-in Pydantic schemas for invoices/receipts
3. **v0.8.5 Integrations** — LlamaIndex + LangChain parsers
4. **Documentation** — Quickstart <5 min, comparison table, badges
5. **Show HN + Reddit posts** at v1.0.0

> Your plugin + hooks architecture is already superior for extensibility. Nail "it just works locally on invoices" and the stars will follow.
> ]()
