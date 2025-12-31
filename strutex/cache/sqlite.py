"""
SQLite-based persistent cache implementation.

Durable, lightweight cache that persists across restarts.
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .base import Cache, CacheKey, CacheEntry

logger = logging.getLogger("strutex.cache.sqlite")


class SQLiteCache(Cache):
    """
    Persistent SQLite cache.
    
    Features:
    - Persistent storage across restarts
    - Automatic table creation
    - TTL support with lazy cleanup
    - Thread-safe (SQLite handles locking)
    
    Example:
        >>> cache = SQLiteCache("~/.cache/strutex/cache.db", ttl=86400)  # 1 day
        >>> 
        >>> key = CacheKey.create("doc.pdf", "Extract", schema, "gemini")
        >>> cache.set(key, {"invoice_number": "INV-001"})
        >>> 
        >>> # Result persists across restarts
        >>> result = cache.get(key)
    """
    
    def __init__(
        self,
        db_path: str = "~/.cache/strutex/cache.db",
        ttl: Optional[float] = None,
        max_size: Optional[int] = None
    ):
        """
        Args:
            db_path: Path to SQLite database file
            ttl: Default TTL in seconds (None = never expire)
            max_size: Optional max entries (enforced on set)
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.default_ttl = ttl
        self.max_size = max_size
        
        # Track cache hits/misses (in-memory, resets on restart)
        self._hits = 0
        self._misses = 0
        
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    result TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL,
                    hit_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires 
                ON cache(expires_at)
            """)
            conn.commit()
        
        logger.debug(f"SQLite cache initialized: {self.db_path}")
    
    def get(self, key: CacheKey) -> Optional[Any]:
        """Get a cached result."""
        key_str = key.to_string()
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT result, expires_at, hit_count
                FROM cache 
                WHERE key = ?
                """,
                (key_str,)
            )
            row = cursor.fetchone()
            
            if row is None:
                self._misses += 1
                return None
            
            result_json, expires_at, hit_count = row
            
            # Check expiration
            if expires_at is not None and now > expires_at:
                conn.execute("DELETE FROM cache WHERE key = ?", (key_str,))
                conn.commit()
                self._misses += 1
                logger.debug(f"Cache expired: {key_str[:32]}")
                return None
            
            # Update hit count
            conn.execute(
                "UPDATE cache SET hit_count = ? WHERE key = ?",
                (hit_count + 1, key_str)
            )
            conn.commit()
            
            self._hits += 1
            logger.debug(f"Cache hit: {key_str[:32]}")
            return json.loads(result_json)
    
    def set(self, key: CacheKey, result: Any, ttl: Optional[float] = None) -> None:
        """Store a result."""
        key_str = key.to_string()
        actual_ttl = ttl if ttl is not None else self.default_ttl
        
        now = time.time()
        expires_at = now + actual_ttl if actual_ttl is not None else None
        result_json = json.dumps(result)
        
        with sqlite3.connect(self.db_path) as conn:
            # Enforce max_size if set
            if self.max_size is not None:
                cursor = conn.execute("SELECT COUNT(*) FROM cache")
                count = cursor.fetchone()[0]
                
                if count >= self.max_size:
                    # Delete oldest entries
                    to_delete = count - self.max_size + 1
                    conn.execute(
                        """
                        DELETE FROM cache 
                        WHERE key IN (
                            SELECT key FROM cache 
                            ORDER BY created_at ASC 
                            LIMIT ?
                        )
                        """,
                        (to_delete,)
                    )
            
            conn.execute(
                """
                INSERT OR REPLACE INTO cache 
                (key, result, created_at, expires_at, hit_count, metadata)
                VALUES (?, ?, ?, ?, 0, NULL)
                """,
                (key_str, result_json, now, expires_at)
            )
            conn.commit()
        
        logger.debug(f"Cache set: {key_str[:32]}")
    
    def delete(self, key: CacheKey) -> bool:
        """Delete a cached entry."""
        key_str = key.to_string()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE key = ?",
                (key_str,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def clear(self) -> int:
        """Clear all cached entries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cache")
            count = cursor.fetchone()[0]
            
            conn.execute("DELETE FROM cache")
            conn.commit()
            
            logger.info(f"Cache cleared: {count} entries")
            return count
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*), SUM(hit_count) FROM cache"
            )
            size, total_hits = cursor.fetchone()
            total_hits = total_hits or 0
            
            cursor = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),)
            )
            expired = cursor.fetchone()[0]
            
            # Calculate hit rate
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            
            return {
                "type": "sqlite",
                "path": str(self.db_path),
                "size": size,
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
                "total_hits_persisted": total_hits,
                "expired_pending": expired,
                "ttl": self.default_ttl,
            }
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),)
            )
            count = cursor.rowcount
            conn.commit()
            
            if count > 0:
                logger.debug(f"Cleaned up {count} expired entries")
            
            return count
    
    def vacuum(self) -> None:
        """Reclaim disk space after deletions."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("VACUUM")
        logger.debug("Cache vacuumed")
