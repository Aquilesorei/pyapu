#!/usr/bin/env python3
"""
Example: Processing Context for Multi-Step Workflows

This example demonstrates how to use ProcessingContext for
stateful, multi-step document processing workflows.
"""

from strutex import ProcessingContext, BatchContext
from strutex.schemas import INVOICE_US, RECEIPT


def example_basic_context():
    """Basic context with state management."""
    print("=" * 60)
    print("Example 1: Basic Context Usage")
    print("=" * 60)
    
    ctx = ProcessingContext()
    
    # Store state
    ctx.set("vendor_id", "ACME-001")
    ctx.set("expected_total", 1500.00)
    ctx.set("items", ["Widget A", "Widget B"])
    
    # Retrieve state
    vendor = ctx.get("vendor_id")
    total = ctx.get("expected_total")
    items = ctx.get("items", default=[])
    
    print(f"Context: {ctx}")
    print(f"Vendor: {vendor}")
    print(f"Expected total: ${total}")
    print(f"Items: {items}")
    
    # Check if key exists
    print(f"Has vendor_id: {ctx.has('vendor_id')}")
    print(f"Has missing_key: {ctx.has('missing_key')}")
    
    return ctx


def example_multi_step_workflow():
    """Multi-step extraction with shared state."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-Step Workflow")
    print("=" * 60)
    
    print("""
    from strutex import DocumentProcessor, ProcessingContext
    from strutex.schemas import INVOICE_US, RECEIPT
    
    processor = DocumentProcessor(provider="gemini")
    ctx = ProcessingContext()
    
    # Step 1: Extract invoice
    invoice = ctx.extract(processor, "invoice.pdf", "Extract invoice", INVOICE_US)
    
    # Store for next step
    ctx.set("invoice_number", invoice.invoice_number)
    ctx.set("expected_total", invoice.total)
    
    # Step 2: Verify receipt matches
    receipt = ctx.extract(
        processor,
        "receipt.jpg",
        f"Verify total matches ${ctx.get('expected_total')}",
        RECEIPT
    )
    
    # Check results
    print(f"Invoice: {ctx.get('invoice_number')}")
    print(f"Receipt total: {receipt.total}")
    print(f"Match: {receipt.total == ctx.get('expected_total')}")
    """)


def example_history_tracking():
    """Tracking extraction history."""
    print("\n" + "=" * 60)
    print("Example 3: History Tracking")
    print("=" * 60)
    
    ctx = ProcessingContext(context_id="demo-001")
    
    # Simulate some history (in real use, ctx.extract() populates this)
    from strutex.context import ExtractionStep
    
    step1 = ExtractionStep(
        step_id="demo-001-1",
        file_path="invoice.pdf",
        prompt="Extract invoice",
        provider="GeminiProvider",
        result={"invoice_number": "INV-001"},
        duration_ms=2150.0
    )
    
    step2 = ExtractionStep(
        step_id="demo-001-2",
        file_path="receipt.jpg",
        prompt="Extract receipt",
        provider="GeminiProvider",
        result={"total": 150.00},
        duration_ms=1800.0
    )
    
    ctx._history.append(step1)
    ctx._history.append(step2)
    
    # Access history
    print(f"Total steps: {len(ctx.history)}")
    for step in ctx.history:
        print(f"  {step.step_id}: {step.file_path} ({step.duration_ms:.0f}ms)")
    
    # Metrics
    print(f"\nMetrics:")
    print(f"  Total duration: {ctx.total_duration_ms:.0f}ms")
    print(f"  Success count: {ctx.success_count}")
    print(f"  Error count: {ctx.error_count}")


def example_step_listeners():
    """Listening to extraction events."""
    print("\n" + "=" * 60)
    print("Example 4: Step Listeners")
    print("=" * 60)
    
    ctx = ProcessingContext()
    
    # Add listener
    def log_step(step):
        if step.error:
            print(f"FAILED: {step.file_path} - {step.error}")
        else:
            print(f"SUCCESS: {step.file_path} ({step.duration_ms:.0f}ms)")
    
    ctx.on_step(log_step)
    
    print("Listener registered!")
    print("Each extraction will now trigger the callback.")
    print("""
    # When you call:
    ctx.extract(processor, "doc.pdf", "Extract", schema)
    
    # Output:
    # SUCCESS: doc.pdf (2150ms)
    """)


def example_batch_context():
    """Batch processing with progress tracking."""
    print("\n" + "=" * 60)
    print("Example 5: Batch Processing")
    print("=" * 60)
    
    # Simulate batch context
    ctx = BatchContext(total_documents=10, context_id="batch-001")
    
    # Simulate some processing
    from strutex.context import ExtractionStep
    
    for i in range(4):
        step = ExtractionStep(
            step_id=f"batch-001-{i+1}",
            file_path=f"doc{i+1}.pdf",
            prompt="Extract",
            provider="GeminiProvider",
            result={"data": f"result{i+1}"},
            duration_ms=2000.0 + (i * 100)
        )
        ctx._history.append(step)
    
    # Progress tracking
    print(f"Progress: {ctx.progress}/{ctx.total_documents}")
    print(f"Progress %: {ctx.progress_percent:.1f}%")
    print(f"Success rate: {ctx.success_rate:.1f}%")
    print(f"Avg duration: {ctx.average_duration_ms:.0f}ms")
    print(f"Est. remaining: {ctx.estimated_remaining_ms / 1000:.1f}s")


def example_serialization():
    """Exporting context for logging/debugging."""
    print("\n" + "=" * 60)
    print("Example 6: Serialization")
    print("=" * 60)
    
    ctx = ProcessingContext(
        context_id="export-demo",
        metadata={"source": "example", "version": "1.0"}
    )
    
    ctx.set("key1", "value1")
    ctx.set("key2", 123)
    
    # Serialize to dict
    data = ctx.to_dict()
    
    import json
    print("Serialized context:")
    print(json.dumps(data, indent=2, default=str)[:500] + "...")


if __name__ == "__main__":
    example_basic_context()
    example_multi_step_workflow()
    example_history_tracking()
    example_step_listeners()
    example_batch_context()
    example_serialization()
    
    print("\n" + "=" * 60)
    print("Processing Context Examples Complete!")
    print("=" * 60)
