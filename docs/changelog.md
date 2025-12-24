# Changelog

All notable changes to strutex will be documented here.

---

## v0.3.0 (December 23, 2025)

### 🚀 New Features

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

### 📁 New Files

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

### ✏️ Updated Files

- `strutex/plugins/registry.py` — Complete rewrite for lazy loading
- `strutex/plugins/base.py` — Added version, priority, cost, health_check to all base classes
- `strutex/plugins/__init__.py` — Export new v2 modules
- `strutex/providers/gemini.py` — Added v2 attributes, removed deprecated decorator
- `pyproject.toml` — Added pluggy, click, mike; added CLI entry point
- `mkdocs.yml` — Added version selector config
- `docs/plugins.md` — Rewritten for v0.3.0 features
- `examples/plugin_example.py` — Updated to showcase v2 features

### ⚠️ Deprecations

- `@register` decorator now emits `DeprecationWarning`
  - Use entry points in `pyproject.toml` instead:
    ```toml
    [project.entry-points."strutex.providers"]
    my_provider = "my_package:MyProvider"
    ```

### 📦 New Dependencies

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
