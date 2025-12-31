# Caching

Reduce API costs and speed up repeated extractions with caching.

---

## Enable Caching

Pass a cache instance to DocumentProcessor:

```python
from strutex import DocumentProcessor, MemoryCache, GeminiProvider

processor = DocumentProcessor(
    provider=GeminiProvider(),
    cache=MemoryCache(max_size=100, ttl=3600)  # 1 hour TTL
)

# First call: hits the LLM API
result1 = processor.process("invoice.pdf", "Extract data", schema=MySchema)

# Second call: returns cached result instantly (no API call!)
result2 = processor.process("invoice.pdf", "Extract data", schema=MySchema)
```

---

## Cache Types

### MemoryCache

Fast, in-memory LRU cache. Best for single-process apps.

```python
from strutex import MemoryCache

cache = MemoryCache(
    max_size=100,  # Max entries (LRU eviction)
    ttl=3600       # TTL in seconds (optional)
)

processor = DocumentProcessor(provider=provider, cache=cache)
```

**Features:**

- LRU eviction when full
- Optional TTL (time-to-live)
- Thread-safe
- Hit/miss statistics

### SQLiteCache

Persistent cache that survives restarts.

```python
from strutex import SQLiteCache

cache = SQLiteCache(
    db_path="~/.cache/strutex/cache.db",
    ttl=86400,     # 24 hour TTL
    max_size=1000  # Optional size limit
)

processor = DocumentProcessor(provider=provider, cache=cache)
```

**Features:**

- Persists across restarts
- Automatic table creation
- Lazy TTL cleanup

### FileCache

File-based cache for simple deployments.

```python
from strutex import FileCache

cache = FileCache(
    cache_dir="/tmp/strutex_cache",
    ttl=3600
)
```

---

## How Cache Keys Work

Cache keys are computed from:

- **File content hash** — Same content = same key (even if renamed)
- **Prompt hash** — Different prompts = different keys
- **Schema hash** — Different schemas = different keys
- **Provider + model** — Different providers = different keys

```python
# These produce DIFFERENT cache keys:
processor.process("invoice.pdf", "Extract all", schema=InvoiceSchema)
processor.process("invoice.pdf", "Extract total only", schema=InvoiceSchema)

# This produces the SAME cache key (same content, prompt, schema):
processor.process("invoice.pdf", "Extract all", schema=InvoiceSchema)
processor.process("invoice_copy.pdf", "Extract all", schema=InvoiceSchema)  # Same content
```

---

##  Cache Invalidation Pitfalls

> [!WARNING]
> Caching can cause stale data if you're not careful. Understand when caches invalidate.

### When Cache DOES Invalidate

| Change                 | Invalidates? | Why                  |
| ---------------------- | ------------ | -------------------- |
| File content changes   | Yes          | Content hash changes |
| Prompt changes         | Yes          | Prompt hash changes  |
| Schema adds new fields | Yes          | Schema hash changes  |
| Provider changes       | Yes          | Provider in key      |
| Model changes          | Yes          | Model in key         |

### When Cache Does NOT Invalidate

| Change                          | Invalidates? | Risk                                             |
| ------------------------------- | ------------ | ------------------------------------------------ |
| **Field descriptions change**   | No           | Schema structure same, but extraction may differ |
| **Pydantic validators change**  | No           | Post-processing logic not in key                 |
| **Provider credentials change** | No           | Key uses provider name, not credentials          |
| **Prompt template internals**   | No           | Only final prompt string is hashed               |

### Safe Cache Usage

```python
# DANGER: Schema description changed, but cache returns old extraction
class Invoice_v1(BaseModel):
    total: float = Field(description="Total amount")  # Old

class Invoice_v2(BaseModel):
    total: float = Field(description="Total amount including tax")  # Changed!

# These have THE SAME cache key because structure is identical:
# processor.process(..., model=Invoice_v1)
# processor.process(..., model=Invoice_v2)  # Returns stale cached result!

# FIX: Clear cache when schema semantics change
cache.clear()

# Or use versioned prompts
processor.process(..., prompt="Extract invoice v2", model=Invoice_v2)
```

### Recommendations

1. **Clear cache after schema changes** — Especially description changes
2. **Use TTL** — Don't cache forever: `MemoryCache(ttl=3600)`
3. **Version your prompts** — Include version in prompt string
4. **Test with fresh cache** — After model updates

## Cache Statistics

```python
from strutex import MemoryCache

cache = MemoryCache()
processor = DocumentProcessor(provider=provider, cache=cache)

# After some usage...
stats = cache.stats()
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Size: {stats['size']}")
```

---

## Manual Cache Operations

```python
from strutex import CacheKey, MemoryCache

cache = MemoryCache()

# Create a cache key manually
key = CacheKey.create(
    file_path="invoice.pdf",
    prompt="Extract",
    schema=MySchema,
    provider="gemini"
)

# Check if cached
if cache.has(key):
    result = cache.get(key)
else:
    result = processor.process(...)
    cache.set(key, result)

# Delete specific entry
cache.delete(key)

# Clear all
cache.clear()
```

---

## Next Steps

| Want to...           | Go to...                              |
| -------------------- | ------------------------------------- |
| Add processing hooks | [Processing Hooks](tutorial-hooks.md) |
| Add security checks  | [Security](tutorial-security.md)      |
| Process in batches   | [Batch Processing](tutorial-batch.md) |
