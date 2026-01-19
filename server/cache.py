"""
Redis-based query cache for LLM responses.

Provides a simple wrapper around Redis for caching user queries and their responses
with TTL expiration and automatic eviction.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Tuple
import redis

logger = logging.getLogger(__name__)


class QueryCache:
    """Redis-based cache for query responses."""

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_seconds: int = 3600,
        key_prefix: str = "query:",
        enabled: bool = True,
    ):
        """
        Initialize the query cache.

        Args:
            redis_client: Redis connection instance
            ttl_seconds: Time-to-live in seconds (default: 3600 = 1 hour)
            key_prefix: Prefix for cache keys (default: "query:")
            enabled: Whether caching is enabled (default: True)
        """
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self.enabled = enabled

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for consistent cache keys.

        Args:
            query: Original query string

        Returns:
            Normalized query string (lowercase, stripped, collapsed spaces)
        """
        if not query:
            return ""
        # Convert to lowercase, strip whitespace, collapse multiple spaces
        normalized = " ".join(query.lower().strip().split())
        return normalized

    def _make_key(self, query: str) -> str:
        """
        Create Redis key from normalized query.

        Args:
            query: Query string (will be normalized)

        Returns:
            Redis key string
        """
        normalized = self._normalize_query(query)
        return f"{self.key_prefix}{normalized}"

    def _serialize(self, response: str, latency_ms: float) -> str:
        """
        Serialize response and latency to JSON.

        Args:
            response: LLM response text
            latency_ms: Response latency in milliseconds

        Returns:
            JSON string
        """
        data = {
            "response": response,
            "latency_ms": latency_ms,
            "created_at": datetime.utcnow().isoformat(),
        }
        return json.dumps(data)

    def _deserialize(self, data: str) -> Tuple[str, float]:
        """
        Deserialize JSON to response and latency.

        Args:
            data: JSON string from Redis

        Returns:
            Tuple of (response, latency_ms)
        """
        try:
            obj = json.loads(data)
            return obj["response"], obj["latency_ms"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to deserialize cache data: {e}")
            raise ValueError(f"Invalid cache data format: {e}")

    def get(self, query: str) -> Optional[Tuple[str, float]]:
        """
        Check Redis cache and return cached response if exists.

        Args:
            query: User query string

        Returns:
            Tuple of (response, latency_ms) if cache hit, None if cache miss
        """
        if not self.enabled:
            return None

        try:
            key = self._make_key(query)
            cached_data = self.redis_client.get(key)

            if cached_data:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return self._deserialize(cached_data)
            else:
                logger.debug(f"Cache miss for query: {query[:50]}...")
                return None

        except redis.RedisError as e:
            logger.warning(f"Redis error during cache get: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during cache get: {e}")
            return None

    def set(self, query: str, response: str, latency_ms: float) -> bool:
        """
        Store response in Redis with TTL.

        Args:
            query: User query string
            response: LLM response text
            latency_ms: Response latency in milliseconds

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            key = self._make_key(query)
            value = self._serialize(response, latency_ms)

            # Use SETEX to set key with TTL
            self.redis_client.setex(key, self.ttl_seconds, value)
            logger.debug(f"Cached response for query: {query[:50]}...")
            return True

        except redis.RedisError as e:
            logger.warning(f"Redis error during cache set: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cache set: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache entries matching the key prefix.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Use SCAN to find all keys with prefix (safer than KEYS for production)
            pattern = f"{self.key_prefix}*"
            keys = []
            cursor = 0

            while True:
                cursor, batch = self.redis_client.scan(cursor, match=pattern, count=100)
                keys.extend(batch)
                if cursor == 0:
                    break

            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
            else:
                logger.info("No cache entries to clear")

            return True

        except redis.RedisError as e:
            logger.warning(f"Redis error during cache clear: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cache clear: {e}")
            return False

    def get_stats(self) -> dict:
        """
        Get cache statistics from Redis.

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {"enabled": False, "error": "Cache is disabled"}

        try:
            # Get database size
            db_size = self.redis_client.dbsize()

            # Get memory info
            info = self.redis_client.info("memory")
            memory_used = info.get("used_memory_human", "N/A")
            memory_peak = info.get("used_memory_peak_human", "N/A")

            # Count keys with our prefix
            pattern = f"{self.key_prefix}*"
            cache_keys = 0
            cursor = 0

            while True:
                cursor, batch = self.redis_client.scan(cursor, match=pattern, count=100)
                cache_keys += len(batch)
                if cursor == 0:
                    break

            return {
                "enabled": True,
                "db_size": db_size,
                "cache_keys": cache_keys,
                "memory_used": memory_used,
                "memory_peak": memory_peak,
            }

        except redis.RedisError as e:
            logger.warning(f"Redis error during stats retrieval: {e}")
            return {"enabled": True, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during stats retrieval: {e}")
            return {"enabled": True, "error": str(e)}

    def is_connected(self) -> bool:
        """
        Check Redis connection status.

        Returns:
            True if connected, False otherwise
        """
        if not self.enabled:
            return False

        try:
            return self.redis_client.ping()
        except Exception:
            return False
