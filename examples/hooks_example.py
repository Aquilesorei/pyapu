"""
Example: Using Callback and Decorator Hooks

This example demonstrates the new hook system in strutex v0.4.2+.
Hooks let you intercept the processing pipeline without modifying core code.
"""

from datetime import datetime
import time
from strutex import DocumentProcessor, Object, String, Number


# =============================================================================
# Example 1: Inline Callbacks
# =============================================================================

def example_callbacks():
    """Use callbacks for quick, inline transformations."""
    
    processor = DocumentProcessor(
        provider="gemini",
        # Add instructions to every prompt
        on_pre_process=lambda fp, prompt, schema, mime, ctx: {
            "prompt": f"{prompt}\n\nIMPORTANT: Extract values exactly as they appear."
        },
        # Add metadata to every result
        on_post_process=lambda result, ctx: {
            **result,
            "_processed": True,
            "_timestamp": datetime.now().isoformat()
        },
        # Handle errors gracefully
        on_error=lambda error, fp, ctx: {
            "error": True,
            "message": str(error),
            "file": fp
        }
    )
    
    return processor


# =============================================================================
# Example 2: Decorator Hooks
# =============================================================================

def example_decorators():
    """Use decorators for reusable, named hooks."""
    
    processor = DocumentProcessor(provider="gemini")
    
    @processor.on_pre_process
    def log_start(file_path, prompt, schema, mime_type, context):
        """Log when processing starts and track timing."""
        context["start_time"] = time.time()
        print(f"[{datetime.now():%H:%M:%S}] Starting: {file_path}")
        return None  # Don't modify the prompt
    
    @processor.on_post_process
    def log_complete(result, context):
        """Log completion and add timing metadata."""
        elapsed = time.time() - context.get("start_time", 0)
        print(f"[{datetime.now():%H:%M:%S}] Completed in {elapsed:.2f}s")
        result["_elapsed_seconds"] = round(elapsed, 3)
        return result
    
    @processor.on_error
    def handle_rate_limit(error, file_path, context):
        """Return cached result on rate limit errors."""
        if "rate limit" in str(error).lower():
            print(f"Rate limited! Returning fallback for {file_path}")
            return {"error": "rate_limited", "retry_after": 60}
        return None  # Propagate other errors
    
    return processor


# =============================================================================
# Example 3: Multiple Hooks (Chain of Responsibility)
# =============================================================================

def example_chained_hooks():
    """Chain multiple hooks for complex pipelines."""
    
    processor = DocumentProcessor(provider="gemini")
    
    # Hook 1: Normalize dates
    @processor.on_post_process
    def normalize_dates(result, context):
        """Convert date strings to ISO format."""
        if "date" in result and isinstance(result["date"], str):
            # Simple normalization (real code would use dateparser)
            result["date_normalized"] = result["date"]
        return result
    
    # Hook 2: Validate totals
    @processor.on_post_process
    def validate_totals(result, context):
        """Ensure total matches sum of line items."""
        if "items" in result and "total" in result:
            calculated = sum(item.get("amount", 0) for item in result["items"])
            result["_total_valid"] = abs(result["total"] - calculated) < 0.01
        return result
    
    # Hook 3: Add audit trail
    @processor.on_post_process
    def add_audit_trail(result, context):
        """Add processing audit information."""
        result["_audit"] = {
            "processed_at": datetime.now().isoformat(),
            "file": context.get("file_path"),
            "mime_type": context.get("mime_type")
        }
        return result
    
    return processor


# =============================================================================
# Example 4: Error Recovery Pattern
# =============================================================================

def example_error_recovery():
    """Demonstrate error recovery with fallback strategies."""
    
    processor = DocumentProcessor(provider="gemini")
    cache = {}  # Simple in-memory cache
    
    @processor.on_pre_process
    def check_cache(file_path, prompt, schema, mime_type, context):
        """Check if we have a cached result."""
        context["cache_key"] = f"{file_path}:{hash(str(schema))}"
        context["from_cache"] = False
        return None
    
    @processor.on_post_process
    def update_cache(result, context):
        """Cache successful results."""
        cache[context["cache_key"]] = result
        return result
    
    @processor.on_error
    def try_cache(error, file_path, context):
        """On error, try to return cached result."""
        cache_key = context.get("cache_key")
        if cache_key and cache_key in cache:
            print(f"Returning cached result for {file_path}")
            cached = cache[cache_key].copy()
            cached["_from_cache"] = True
            return cached
        return None  # No cache, propagate error
    
    return processor


# =============================================================================
# Main: Run examples
# =============================================================================

if __name__ == "__main__":
    print("Strutex Hook Examples")
    print("=" * 50)
    
    # Create processor with decorators
    processor = example_decorators()
    
    schema = Object(
        description="Invoice data",
        properties={
            "invoice_number": String(description="Invoice ID"),
            "total": Number(description="Total amount"),
            "date": String(description="Invoice date")
        }
    )
    
    print("\nProcessor configured with hooks:")
    print(f"  - Pre-process hooks: {len(processor._pre_process_hooks)}")
    print(f"  - Post-process hooks: {len(processor._post_process_hooks)}")
    print(f"  - Error hooks: {len(processor._error_hooks)}")
    
    # Note: Actual processing requires a valid file and API key
    # result = processor.process("invoice.pdf", "Extract invoice data", schema)
    
    print("\n✅ Examples loaded successfully!")
    print("To use: modify the processor.process() call with a real file.")
