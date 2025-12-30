# Strutex Roadmap

> **Stru**ctured **T**ext **Ex**traction — Extract structured JSON from documents using LLMs

---

## ✅ Released

| Version    | Focus                 | Highlights                                                                    |
| ---------- | --------------------- | ----------------------------------------------------------------------------- |
| **v1.0.x** | Production Ready      | GLiNER extractor, Ollama vision support, pipeline documentation               |
| v1.0.0     | Stable Release        | Full plugin system, multi-provider, verification loop, caching                |
| v0.8.0     | Caching & Performance | Smart caching (Memory/SQLite), async processing, batch API, verification loop |
| v0.7.0     | Multi-Provider        | OpenAI, Anthropic, Ollama, Groq + provider fallback chains                    |
| v0.6.0     | Built-in Schemas      | 9 ready-to-use schemas (Invoice, Receipt, Bill of Lading, etc.)               |
| v0.3.0     | Plugin System v2      | Auto-registration, lazy loading, CLI tooling                                  |

---

## ✅ Completed Integrations

- [x] **LlamaIndex**: `StrutexParser` node/loader
- [x] **LangChain**: `StrutexLoader` + `StrutexOutputParser`
- [x] **Haystack**: Integration module
- [x] **Unstructured**: Fallback extractor
- [x] **GLiNER**: Fast local entity extraction

---

## 🔥 Coming Next

### v1.1.0 — Reliability & Postprocessing

Production-grade data quality:

- **Confidence scores** per extracted field
- **Postprocessor plugins** (date/number normalization)
- **Hallucination detection** (multi-model voting)

### v1.2.0 — Enterprise Deployment

- **REST API server** (FastAPI) — `strutex serve`
- **Docker image** with OCR pre-configured
- **Human-in-the-loop** callbacks for low-confidence results

---

## 🔮 Future Vision

| Feature                   | Benefit                                                         |
| ------------------------- | --------------------------------------------------------------- |
| **Supplier Intelligence** | Layout caching, skip LLM for known formats (80% cost reduction) |
| **Visual Debugging**      | Export PDFs with bounding boxes showing where fields were found |
| **Schema Discovery**      | AI-suggested Pydantic schemas from sample documents             |
| **Multi-Page Tables**     | Automatic table stitching across pages                          |
| **Local SLM Support**     | Run on-device for privacy-sensitive documents                   |
| **Universal Connectors**  | One-line exports to QuickBooks, SAP, Postgres                   |

---

## Philosophy

**Everything is pluggable.** Strutex provides sensible defaults but lets you replace any component:

```python
from strutex import DocumentProcessor
from strutex.plugins import Provider

# Use defaults
processor = DocumentProcessor(provider="gemini")

# Or plug in your own
class MyProvider(Provider, name="custom"):
    def process(self, ...): ...
```

---

## Contributing

We welcome contributions! Priority areas:

1. **New providers** — Azure, Bedrock, HuggingFace
2. **More schemas** — French/German invoices, medical forms
3. **Extractors** — Better table handling, form detection

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

📚 **[Full Documentation](https://aquilesorei.github.io/strutex/latest/)** | 🐙 **[GitHub](https://github.com/Aquilesorei/strutex)** | 📦 **[PyPI](https://pypi.org/project/strutex/)**
