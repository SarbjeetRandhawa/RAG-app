import os
import time
import logging
from cache.redis_client import redis_client
from cache.serializers import CacheSerializer
from cache.statistics import cache_stats

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.config = {
            "response": os.environ.get("CACHE_RESPONSE", "true").lower() == "true",
            "embedding": os.environ.get("CACHE_EMBEDDINGS", "true").lower() == "true",
            "retrieval": os.environ.get("CACHE_RETRIEVAL", "true").lower() == "true",
            "rerank": os.environ.get("CACHE_RERANK", "true").lower() == "true",
            "evaluation": os.environ.get("CACHE_EVALUATION", "true").lower() == "true",
            "session": os.environ.get("CACHE_SESSIONS", "true").lower() == "true"
        }
        
    def is_enabled(self, namespace: str) -> bool:
        """
        Check if caching is enabled for a specific namespace via environment variables,
        and verify that the Redis client is actually connected and available.
        """
        return self.config.get(namespace, False) and redis_client.is_available()

    def get(self, key: str, namespace: str):
        """
        Retrieve a value from the Redis cache.
        
        Args:
            key (str): The unique cache key.
            namespace (str): The namespace the key belongs to (used for stats tracking).
            
        Returns:
            The deserialized cached value if found (cache hit), otherwise None (cache miss).
        """
        if not self.is_enabled(namespace):
            return None
            
        start_time = time.time()
        try:
            client = redis_client.get_client()
            raw_data = client.get(key)
            latency = (time.time() - start_time) * 1000
            
            if raw_data:
                logger.info(f"[Redis] {namespace.capitalize()} Cache HIT")
                cache_stats.record_hit(namespace, latency)
                return CacheSerializer.deserialize(raw_data)
            else:
                logger.info(f"[Redis] {namespace.capitalize()} Cache MISS")
                cache_stats.record_miss(namespace)
                return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    def set(self, key: str, value, namespace: str, ttl: int = None):
        """
        Store a value in the Redis cache.
        
        Args:
            key (str): The unique cache key.
            value: The data to cache (will be serialized automatically).
            namespace (str): The namespace the key belongs to.
            ttl (int, optional): Time-to-live in seconds before the key expires.
        """
        if not self.is_enabled(namespace):
            return
            
        try:
            client = redis_client.get_client()
            serialized = CacheSerializer.serialize(value)
            if ttl:
                client.setex(key, ttl, serialized)
            else:
                client.set(key, serialized)
            logger.info(f"[Redis] Stored {namespace.capitalize()} Cache")
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")

    def clear_namespace(self, namespace: str):
        """
        Clear all cached keys that belong to a specific namespace, 
        and reset its corresponding statistics.
        """
        if not redis_client.is_available():
            return
        try:
            client = redis_client.get_client()
            keys = client.keys(f"{namespace}:*")
            if keys:
                client.delete(*keys)
            client.delete(f"cache_stats:{namespace}")
            logger.info(f"Cleared cache namespace: {namespace}")
        except Exception as e:
            logger.error(f"Failed to clear namespace {namespace}: {e}")

    def clear_all(self):
        """
        Clear the entire Redis database cache (flushdb).
        """
        if not redis_client.is_available():
            return
        try:
            client = redis_client.get_client()
            client.flushdb()
            logger.info("Cleared all Redis cache")
        except Exception as e:
            logger.error(f"Failed to clear all cache: {e}")

cache_manager = CacheManager()
