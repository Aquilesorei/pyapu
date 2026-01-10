# Processors

Strutex provides 11 specialized extraction strategies. Each processor is optimized for a specific production requirement, from simple one-shot extractions to high-stakes multi-model consensus.

## 1. SimpleProcessor

The standard extraction strategy. It takes a document and a schema, and returns structured data in a single LLM call.

```python
result = processor.simple.process("invoice.pdf", "Extract totals", schema=Invoice)
```

## 2. VerifiedProcessor

Adds a "verification loop" where the LLM reviews and corrects its own output. This significantly reduces hallucinations.

```python
# Enable via 'verify=True' or using the strategy directly
result = processor.process("contract.pdf", "Extract clauses", verify=True)
```

## 3. RagProcessor

Retrieval-Augmented Generation for massive documents that don't fit in a single prompt. It retrieves relevant chunks before extraction.

```python
result = processor.rag.process("large_book.pdf", "Summarize chapter 5")
```

## 4. BatchProcessor

Handles parallel processing of multiple documents using a thread pool. Excellent for high-volume ingest.

```python
batch_context = processor.batch.process(["doc1.pdf", "doc2.pdf"], "Extract titles")
results = batch_context.results
```

## 5. FallbackProcessor

Implements a safety net. It tries multiple providers in order—useful for cost-optimization or ensuring high availability.

```python
fallback = processor.create_fallback(configs=[
    {"provider": "gemini", "model_name": "gemini-2.5-flash"}, # Fast/Cheap
    {"provider": "openai", "model_name": "gpt-4o"}            # Powerful/Reliable
])
result = fallback.process("data.pdf", "Extract")
```

## 6. RouterProcessor

Intelligently classifies a document before processing, routing it to a specialized processor.

```python
router = processor.create_router(routes={"invoice": invoice_proc, "id": id_proc})
result = router.process("unknown.jpg", "Extract")
```

## 7. EnsembleProcessor

Runs multiple models in parallel (e.g., Gemini and GPT-4) and uses a "judge" model to resolve contradictions.

```python
ensemble = processor.create_ensemble(providers=[p1, p2], judge=judge_p)
result = ensemble.process("medical_report.pdf", "Extract diagnosis")
```

## 8. SequentialProcessor

Processes very long documents page-by-page, carrying a "running state" to ensure consistency across the whole file.

```python
sequential = processor.create_sequential(chunk_size_pages=1)
result = sequential.process("legal_bundle.pdf", "Extract timeline")
```

## 9. PrivacyProcessor

Redacts PII (Emails, Phones, SSNs) locally before sending the document to an LLM provider, then restores the data in the final result.

```python
privacy = processor.create_privacy()
result = privacy.process("patient_record.txt", "Extract symptoms")
```

## 10. ActiveLearningProcessor

Assesses extraction confidence. It flags results that require human review based on consistency across multiple trials.

```python
active = processor.create_active(num_trials=3, confidence_threshold=0.9)
result = active.process("blurred_id.jpg", "Extract number")
# result contains "_confidence" and "_requires_review"
```

## 11. AgenticProcessor

The most advanced processor. It uses an autonomous **Plan-Act-Observe** loop (powered by LangGraph) to navigate complex documents using other processors and internal library utilities as tools.

```python
result = processor.agentic.process(
    "100_page_contract.pdf",
    "Find all termination clauses and liability limits across the document"
)
```

## Creating Your Own Strategy

The true power of `strutex` lies in its extensibility. You can create entirely new extraction workflows by inheriting from `strutex.processors.base.Processor`.

By inheriting from the base class, your custom processor automatically gains:

- **Automatic Provider Resolution**: Handle string names or provider instances.
- **Global Hooks**: Pre-process, post-process, and error hooks execution.
- **Validation Infrastructure**: Built-in support for Pydantic and native schemas.
- **Security Integration**: Automatic execution of security plugins.

### Example: A custom "Debug" Processor

```python
from strutex.processors import Processor
from typing import Any, Optional

class DebugProcessor(Processor):
    def process(self, file_path: str, prompt: str, **kwargs) -> Any:
        print(f"DEBUG: Processing {file_path}")
        # Your custom logic here
        return {"status": "debug_ok"}

    async def aprocess(self, file_path: str, prompt: str, **kwargs) -> Any:
        # Async implementation
        return await super().aprocess(file_path, prompt, **kwargs)
```
