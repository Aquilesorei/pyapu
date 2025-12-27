# Caching

Reduce API costs and improve response times with strutex's caching system.

---

## Quick Start

```python
from strutex import DocumentProcessor, MemoryCache
from strutex.schemas import INVOICE_US

# Create processor with cache
processor = DocumentProcessor(
    provider="gemini",
    cache=MemoryCache(max_size=100, ttl=3600)  # 1 hour TTL
)

# First call: hits LLM API
result1 = processor.process("invoice.pdf", "Extract invoice", model=INVOICE_US)

# Second call: returns cached result instantly (no API call)
result2 = processor.process("invoice.pdf", "Extract invoice", model=INVOICE_US)

print(f"Invoice: {result1}")
```

The cache key is automatically computed from:

- File content hash (same content = same key)
- Prompt hash
- Schema hash
- Provider and model name

---

## Manual Cache Usage

For more control, you can manually manage the cache:

```python
from strutex import DocumentProcessor, MemoryCache, CacheKey

cache = MemoryCache()
processor = DocumentProcessor(provider="gemini")

# Create cache key
key = CacheKey.create("invoice.pdf", "Extract invoice", INVOICE_US, "gemini")

# Check cache
result = cache.get(key)
if result is None:
    result = processor.process("invoice.pdf", "Extract invoice", model=INVOICE_US)
    cache.set(key, result)
```

---

## Cache Types

### MemoryCache

Fast, in-memory LRU cache. Best for single-process applications.

```python
from strutex import MemoryCache

cache = MemoryCache(
    max_size=100,   # Max entries (LRU eviction)
    ttl=3600        # TTL in seconds (optional)
)

# Thread-safe operations
cache.set(key, result)
result = cache.get(key)
```

**Features:**

- LRU eviction when max_size reached
- Optional TTL (time-to-live)
- Thread-safe
- Hit/miss statistics

### SQLiteCache

Persistent cache that survives restarts. Best for durability.

```python
from strutex import SQLiteCache

cache = SQLiteCache(
    db_path="~/.cache/strutex/cache.db",
    ttl=86400,      # 24 hour TTL
    max_size=1000   # Optional size limit
)

# Persists across restarts
cache.set(key, result)
```

**Features:**

- Persistent storage
- Automatic table creation
- Lazy TTL cleanup
- Size limits with oldest-first eviction

### FileCache

Simple JSON file cache. Best for debugging and portability.

```python
from strutex import FileCache

cache = FileCache(
    cache_dir="~/.cache/strutex/files/",
    ttl=3600
)

# Each entry is a separate JSON file
cache.set(key, result)  # Creates {hash}.json
```

**Features:**

- One JSON file per entry
- Easy to inspect/debug
- Portable across systems

---

## CacheKey

Cache keys are computed from:

- **File content hash** (SHA256 of file bytes)
- **Prompt hash** (SHA256 of prompt text)
- **Schema hash** (SHA256 of schema structure)
- **Provider name**
- **Model name** (optional)

```python
from strutex import CacheKey

# Create from extraction parameters
key = CacheKey.create(
    file_path="invoice.pdf",
    prompt="Extract invoice details",
    schema=INVOICE_US,
    provider="gemini",
    model="gemini-2.5-flash"
)

# Key string: "a1b2c3:d4e5f6:g7h8i9:gemini:gemini-2.5-flash"
print(key.to_string())
```

!!! note "Content-based Keys"
Keys are based on file **content**, not filename. Same file under different names = same cache entry.

---

## Cache Statistics

All caches provide statistics:

```python
stats = cache.stats()
print(f"Cache size: {stats['size']}")
print(f"Hit rate: {stats['hit_rate']}%")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
```

**MemoryCache stats:**

```python
{
    "type": "memory",
    "size": 42,
    "max_size": 100,
    "hits": 150,
    "misses": 20,
    "hit_rate": 88.24,
    "ttl": 3600
}
```

---

## Cache Maintenance

### Clear all entries

```python
count = cache.clear()
print(f"Cleared {count} entries")
```

### Clean up expired entries

```python
count = cache.cleanup_expired()
print(f"Removed {count} expired entries")
```

### Vacuum SQLite (reclaim disk space)

```python
sqlite_cache.vacuum()
```

---

## Wrapper Pattern

Create a cached processor wrapper:

```python
class CachedProcessor:
    def __init__(self, processor, cache):
        self.processor = processor
        self.cache = cache

    def process(self, file_path, prompt, schema, **kwargs):
        # Generate cache key
        provider = self.processor.provider.__class__.__name__
        key = CacheKey.create(file_path, prompt, schema, provider)

        # Try cache first
        result = self.cache.get(key)
        if result is not None:
            return result

        # Call API and cache result
        result = self.processor.process(file_path, prompt, schema=schema, **kwargs)
        self.cache.set(key, result)
        return result

# Usage
processor = DocumentProcessor(provider="gemini")
cached = CachedProcessor(processor, MemoryCache(max_size=100))
result = cached.process("invoice.pdf", "Extract", INVOICE_US)
```

---

## Best Practices

1. **Choose the right cache type:**

   - `MemoryCache` for speed
   - `SQLiteCache` for persistence
   - `FileCache` for debugging

2. **Set appropriate TTLs:**

   - Short TTL for dynamic content
   - Long TTL for static documents

3. **Monitor hit rates:**

   - Low hit rate = check key generation
   - High miss rate = increase cache size

4. **Clean up regularly:**

   - Call `cleanup_expired()` periodically
   - Use `vacuum()` for SQLite after deletes

5. **Don't cache errors:**
   - Only cache successful results
   - Let failed requests retry
