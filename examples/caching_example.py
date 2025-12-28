#!/usr/bin/env python3
"""
Example: Caching for Cost Reduction

This example demonstrates how to use strutex's caching system
to reduce API costs and improve response times.
"""

from strutex import (
    DocumentProcessor,
    MemoryCache,
    SQLiteCache,
    FileCache,
    CacheKey,
)
from strutex.schemas import INVOICE_US


def example_memory_cache():
    """In-memory LRU cache with TTL."""
    print("=" * 60)
    print("Example 1: Memory Cache")
    print("=" * 60)
    
    # Create cache with 100 entries max, 1 hour TTL
    cache = MemoryCache(max_size=100, ttl=3600)
    
    # Simulate creating a cache key
    key = CacheKey(
        file_hash="abc123",
        prompt_hash="def456",
        schema_hash="ghi789",
        provider="gemini"
    )
    
    # Store a result
    cache.set(key, {"invoice_number": "INV-001", "total": 1500.00})
    
    # Retrieve it
    result = cache.get(key)
    print(f"Cached result: {result}")
    
    # Check stats
    stats = cache.stats()
    print(f"Cache stats: {stats}")
    
    return cache


def example_real_cache_key():
    """Create cache key from actual file."""
    print("\n" + "=" * 60)
    print("Example 2: Real Cache Keys")
    print("=" * 60)
    
    # In real usage, CacheKey.create() hashes the actual file content
    print("""
    from strutex import CacheKey
    from strutex.schemas import INVOICE_US
    
    key = CacheKey.create(
        file_path="invoice.pdf",
        prompt="Extract all invoice details",
        schema=INVOICE_US,
        provider="gemini",
        model="gemini-3-flash-preview"
    )
    
    print(key.to_string())
    # Output: a1b2c3:d4e5f6:g7h8i9:gemini:gemini-3-flash-preview
    """)


def example_sqlite_cache():
    """Persistent SQLite cache."""
    print("\n" + "=" * 60)
    print("Example 3: SQLite Cache (Persistent)")
    print("=" * 60)
    
    # Create persistent cache
    cache = SQLiteCache(
        db_path="/tmp/strutex_example_cache.db",
        ttl=86400,      # 24 hours
        max_size=1000   # Max 1000 entries
    )
    
    key = CacheKey(
        file_hash="xyz789",
        prompt_hash="abc123",
        schema_hash="def456",
        provider="openai"
    )
    
    # Store and retrieve
    cache.set(key, {"data": "persists across restarts"})
    result = cache.get(key)
    print(f"SQLite cache result: {result}")
    
    # Stats
    stats = cache.stats()
    print(f"SQLite stats: {stats}")
    
    # Cleanup
    cache.cleanup_expired()
    
    return cache


def example_file_cache():
    """File-based JSON cache."""
    print("\n" + "=" * 60)
    print("Example 4: File Cache (Easy to Inspect)")
    print("=" * 60)
    
    cache = FileCache(
        cache_dir="/tmp/strutex_file_cache/",
        ttl=3600
    )
    
    key = CacheKey(
        file_hash="file123",
        prompt_hash="prompt456",
        schema_hash="schema789",
        provider="anthropic"
    )
    
    cache.set(key, {"easy": "to inspect", "files": "as JSON"})
    result = cache.get(key)
    print(f"File cache result: {result}")
    print(f"Cache directory: {cache.cache_dir}")
    
    return cache


def example_cached_processor():
    """Wrapper pattern for cached processing."""
    print("\n" + "=" * 60)
    print("Example 5: Cached Processor Pattern")
    print("=" * 60)
    
    print("""
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
                print("Cache HIT!")
                return result
            
            # Cache miss - call API
            print("Cache MISS - calling API...")
            result = self.processor.process(
                file_path, prompt, schema=schema, **kwargs
            )
            
            # Cache the result
            self.cache.set(key, result)
            return result
    
    # Usage
    processor = DocumentProcessor(provider="gemini")
    cache = MemoryCache(max_size=100)
    cached = CachedProcessor(processor, cache)
    
    # First call - cache miss
    result1 = cached.process("invoice.pdf", "Extract", INVOICE_US)
    
    # Second call - cache hit (no API call!)
    result2 = cached.process("invoice.pdf", "Extract", INVOICE_US)
    """)


def example_cache_maintenance():
    """Cache maintenance operations."""
    print("\n" + "=" * 60)
    print("Example 6: Cache Maintenance")
    print("=" * 60)
    
    cache = MemoryCache(max_size=10, ttl=1)  # 1 second TTL for demo
    
    # Add some entries
    for i in range(5):
        key = CacheKey(
            file_hash=f"file{i}",
            prompt_hash="prompt",
            schema_hash="schema",
            provider="test"
        )
        cache.set(key, {"index": i})
    
    print(f"Cache size: {cache.stats()['size']}")
    
    # Cleanup expired (would remove entries after TTL)
    import time
    time.sleep(1.5)  # Wait for expiry
    expired = cache.cleanup_expired()
    print(f"Cleaned up {expired} expired entries")
    
    # Clear all
    cleared = cache.clear()
    print(f"Cleared {cleared} entries")


if __name__ == "__main__":
    example_memory_cache()
    example_real_cache_key()
    example_sqlite_cache()
    example_file_cache()
    example_cached_processor()
    example_cache_maintenance()
    
    print("\n" + "=" * 60)
    print("Caching Examples Complete!")
    print("=" * 60)
