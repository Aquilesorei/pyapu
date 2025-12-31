# Changelog

All notable changes to strutex will be documented here.

---

## v0.8.1 (December 26, 2025)

### 🐛 Bug Fixes & Improvements

- **Documentation**: Updated README with "What's New" and PyPI links.
- **Coverage**: Increased test coverage >61% (OpenAI/Langdock tests).
- **Docs**: Added `docs/caching.md`.

---

## v0.8.0 (December 26, 2025)

###  New Features

**Core Processing Enhancements**

- **Async Support**: `aprocess()` on `DocumentProcessor` and all Providers for high-concurrency apps.
- **Batch Processing**: `process_batch()` and `aprocess_batch()` for efficient multi-document handling.
- **Token & Cost Tracking**: Usage statistics (tokens, cost) aggregated in `ProcessingContext`.
- **Hybrid Fallback**: `HybridProvider` robustly falls back to local PDF text extraction if LLM fails.
- **Verification**: `verify()` method and `process(verify=True)` for LLM-based self-correction and auditing of results.

**Cache System**

- `MemoryCache` — In-memory LRU cache with TTL and thread-safety
- `SQLiteCache` — Persistent SQLite-based cache with lazy cleanup
- `FileCache` — Simple file-based JSON cache for debugging
- `CacheKey` — Smart hashing of file content + prompt + schema + provider
- Cache statistics tracking (hits, misses, hit rate)
- Automatic expiration and cleanup

**Processing Context**

- `ProcessingContext` — State management for multi-step workflows
- `BatchContext` — Progress tracking for batch processing
- Extraction history with timing and error tracking
- Step listeners for monitoring and logging
- Serialization for debugging and persistence

**Streaming Support**

- `StreamingProcessor` — Real-time response streaming
- `StreamChunk` — Typed streaming chunks
- `stream_to_string()` / `stream_with_callback()` utilities
- Async streaming support

###  New Files

- `strutex/extractors/pdf.py` — PDF Extractor (pdfplumber)
- `strutex/providers/hybrid.py` — Hybrid Provider
- `strutex/cache/__init__.py` — Cache module
- `strutex/cache/base.py` — Cache interface and CacheKey
- `strutex/cache/memory.py` — MemoryCache
- `strutex/cache/sqlite.py` — SQLiteCache
- `strutex/cache/file.py` — FileCache
- `strutex/context.py` — ProcessingContext and BatchContext
- `strutex/providers/streaming.py` — Streaming support
- `docs/cache.md` — Caching documentation
- `docs/context.md` — Context documentation
- `docs/streaming.md` — Streaming documentation
- `examples/caching_example.py`
- `examples/context_example.py`

---

## v0.7.0 (December 26, 2025)

###  New Features

**Multi-Provider Support**

- `OpenAIProvider` — GPT-4o and GPT-4 Vision support
- `AnthropicProvider` — Claude 3.5 Sonnet and Claude 3 Opus
- `OllamaProvider` — Local models via Ollama (free, air-gapped)
- `GroqProvider` — Ultra-fast inference at low cost

**Provider Chains**

- `ProviderChain` — Automatic fallback between providers
- `local_first_chain()` — Ollama → Gemini → OpenAI
- `cost_optimized_chain()` — Providers ordered by cost
- `create_fallback_chain()` — Quick chain creation
- Fallback callbacks for monitoring
- `last_provider` property for tracking

**Retry Infrastructure**

- `RetryConfig` — Configurable retry with exponential backoff
- `with_retry()` decorator for sync/async functions
- `RateLimiter` — Simple rate limiting for API calls

###  New Files

- `strutex/providers/openai.py` — OpenAI provider
- `strutex/providers/anthropic.py` — Anthropic provider
- `strutex/providers/ollama.py` — Ollama provider
- `strutex/providers/groq.py` — Groq provider
- `strutex/providers/chain.py` — Provider chain
- `strutex/providers/retry.py` — Retry utilities
- `docs/providers.md` — Updated provider documentation
- `docs/provider-chains.md` — Chain documentation
- `examples/provider_chain_example.py`

---

## v0.6.0 (December 26, 2025)

###  New Features

**Built-in Schemas Module**

- 9 ready-to-use Pydantic schemas for common document types:
  - `INVOICE_GENERIC`, `INVOICE_US`, `INVOICE_EU`
  - `RECEIPT`, `PURCHASE_ORDER`, `BILL_OF_LADING`
  - `BANK_STATEMENT`, `RESUME`, `CONTRACT_CLAUSE`
- One-line imports: `from strutex.schemas import INVOICE_US`
- Schema inheritance for customization

**Logging Module**

- `strutex.logging` module with standardized logging
- `get_logger()`, `configure_logging()`, `set_level()`
- Environment variable support: `STRUTEX_LOG_LEVEL`

**CI/CD Improvements**

- pytest-cov for coverage reporting
- Codecov integration
- mypy type checking (non-blocking)
- Coverage badge in README

###  New Files

- `strutex/schemas/__init__.py` — Schema exports
- `strutex/schemas/invoice.py` — Invoice schemas
- `strutex/schemas/receipt.py` — Receipt schema
- `strutex/schemas/purchase_order.py` — PO schema
- `strutex/schemas/shipping.py` — Bill of Lading
- `strutex/schemas/financial.py` — Bank Statement
- `strutex/schemas/resume.py` — Resume schema
- `strutex/schemas/legal.py` — Contract clauses
- `strutex/logging.py` — Logging module
- `docs/schemas.md` — Schema documentation
- `examples/schemas_example.py`

---

## v0.3.0 (December 23, 2025)

###  New Features

**Plugin System v2**

- **Lazy Loading**: Plugins are only imported when first used via `PluginRegistry.get()`, improving startup time
- **Entry Points**: Register plugins via `pyproject.toml` entry points (recommended over `@register` decorator)
- **API Versioning**: All plugins have `strutex_plugin_version = "1.0"` attribute for compatibility checks
- **Priority Ordering**: Plugins declare `priority` (0-100) for waterfall ordering; higher = preferred
- **Cost Hints**: Plugins declare `cost` for optimization; lower = cheaper
- **Health Checks**: All base classes have `health_check()` classmethod
- **Protocol Types**: `ProviderProtocol`, `ValidatorProtocol`, etc. for mypy-compatible type checking
- **Discovery Caching**: Plugin discovery cached in `~/.cache/strutex/plugins.json`, invalidated on pip changes
- **Sandboxed Probing**: `sandbox.py` for safely probing untrusted plugins in subprocess

**CLI Tooling**

- `strutex plugins list` — Show all discovered plugins with health status
- `strutex plugins list --type provider` — Filter by plugin type
- `strutex plugins list --json` — JSON output for scripting
- `strutex plugins info <name> --type <type>` — Detailed plugin info
- `strutex plugins refresh` — Re-scan entry points and refresh cache
- `strutex plugins cache` — Show/clear discovery cache

**Pluggy Hooks**

- `@hookimpl` decorator for pipeline extension
- `strutex_pre_process` — Called before document processing
- `strutex_post_process` — Called after processing, can transform results
- `strutex_on_error` — Called on failure for error recovery

**Documentation**

- Versioned documentation with mike
- Version selector dropdown in docs
- Automated docs deployment via GitHub Actions
- New changelog page

### New Files

- `strutex/plugins/protocol.py` — Protocol-typed interfaces
- `strutex/plugins/hooks.py` — Pluggy hook specifications
- `strutex/plugins/discovery.py` — Cached plugin discovery
- `strutex/plugins/sandbox.py` — Subprocess plugin probing
- `strutex/cli.py` — CLI commands
- `tests/test_plugin_contract.py` — Contract tests for plugins
- `tests/test_v030_features.py` — v0.3.0 feature tests
- `.github/workflows/docs.yml` — Automated docs deployment
- `docs/changelog.md` — This changelog
- `docs/hooks.md` — Hooks system documentation
- `docs/cli.md` — CLI commands documentation

### Updated Files

- `strutex/plugins/registry.py` — Complete rewrite for lazy loading
- `strutex/plugins/base.py` — Added version, priority, cost, health_check to all base classes
- `strutex/plugins/__init__.py` — Export new v2 modules
- `strutex/providers/gemini.py` — Added v2 attributes, removed deprecated decorator
- `pyproject.toml` — Added pluggy, click, mike; added CLI entry point
- `mkdocs.yml` — Added version selector config
- `docs/plugins.md` — Rewritten for v0.3.0 features
- `examples/plugin_example.py` — Updated to showcase v2 features

### Deprecations

- `@register` decorator now emits `DeprecationWarning`
  - Use entry points in `pyproject.toml` instead:
    ```toml
    [project.entry-points."strutex.providers"]
    my_provider = "my_package:MyProvider"
    ```

### New Dependencies

- `pluggy ^1.5.0` — Hook system (battle-tested, from pytest team)
- `click ^8.1.0` — CLI framework
- `mike ^2.1.0` — Documentation versioning (dev dependency)

---

## v0.2.0

### Features

- Plugin registry system with `@register` decorator
- Security plugins: `InputSanitizer`, `PromptInjectionDetector`, `OutputValidator`
- Composable `SecurityChain`
- Pydantic model support for schemas
- Base classes: `Provider`, `Extractor`, `Validator`, `Postprocessor`, `SecurityPlugin`

---

## v0.1.0

### Initial Release

- Google Gemini provider
- Custom schema types (`Object`, `String`, `Number`, `Array`, `Boolean`)
- PDF text extraction with waterfall fallback (pypdf → pdfplumber → pdfminer → OCR)
- Excel/spreadsheet support
- MIME type detection
- `StructuredPrompt` fluent builder API
