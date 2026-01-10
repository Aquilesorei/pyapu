"""
Showcase of Advanced Processors in Strutex.

This example demonstrates how to use the 6 new advanced processors:
1. FallbackProcessor
2. RouterProcessor
3. EnsembleProcessor
4. SequentialProcessor
5. PrivacyProcessor
6. ActiveLearningProcessor
"""

import os
from strutex import DocumentProcessor
from strutex.types import Object, String

# 1. Setup Sample Data
with open("sample.txt", "w") as f:
    f.write("Invoice #12345 from ACME Corp. Total: $500. Contact: support@acme.com")

# Initialize the main processor facade
dp = DocumentProcessor(provider="gemini")

# ---------------------------------------------------------
# 1. FallbackProcessor: Reliability & Cost Optimization
# ---------------------------------------------------------
print("\n--- 1. FallbackProcessor ---")
fallback = dp.create_fallback(configs=[
    {"provider": "gemini", "model_name": "gemini-1.5-flash"}, # Fast/Cheap target
    {"provider": "openai", "model_name": "gpt-4o"}            # High-reliability backup
])
# result = fallback.process("sample.txt", "Extract total amount")
print("Fallback ready with Gemini -> OpenAI backup.")

# ---------------------------------------------------------
# 2. RouterProcessor: Content-Based Routing
# ---------------------------------------------------------
print("\n--- 2. RouterProcessor ---")
def classify_doc(content: str) -> str:
    if "invoice" in content.lower():
        return "invoice"
    return "general"

router = dp.create_router(
    routes={
        "invoice": dp.simple,
        "general": dp.simple
    },
    classifier=classify_doc
)
# result = router.process("sample.txt", "Extract data")
print("Router configured to detect 'invoice' type.")

# ---------------------------------------------------------
# 3. EnsembleProcessor: Multi-Model Consensus
# ---------------------------------------------------------
print("\n--- 3. EnsembleProcessor ---")
# Use multiple providers and a judge to synthesize the best result
ensemble = dp.create_ensemble(
    providers=["gemini", "openai"],
    judge="gemini"
)
print("Ensemble ready (Gemini + OpenAI with Gemini as judge).")

# ---------------------------------------------------------
# 4. SequentialProcessor: Page-by-Page Processing
# ---------------------------------------------------------
print("\n--- 4. SequentialProcessor ---")
# Ideal for very long documents that exceed prompt limits
sequential = dp.create_sequential(chunk_size_pages=2)
print("Sequential processor ready for long document processing.")

# ---------------------------------------------------------
# 5. PrivacyProcessor: Local PII Redaction
# ---------------------------------------------------------
print("\n--- 5. PrivacyProcessor ---")
privacy = dp.create_privacy()
# This will redact 'support@acme.com' before sending to the LLM
# result = privacy.process("sample.txt", "Extract contact email")
print("Privacy processor configured for local PII redaction.")

# ---------------------------------------------------------
# 6. ActiveLearningProcessor: Confidence & Review
# ---------------------------------------------------------
print("\n--- 6. ActiveLearningProcessor ---")
active = dp.create_active(num_trials=3, confidence_threshold=0.85)
# result = active.process("sample.txt", "Extract invoice number")
# Flags result['_requires_review'] = True if LLM output is inconsistent
print("Active Learning processor ready with multi-trial consistency check.")

print("\nAll advanced processors configured successfully!")
os.remove("sample.txt")
