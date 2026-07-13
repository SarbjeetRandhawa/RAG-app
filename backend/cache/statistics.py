import time
import logging
from cache.redis_client import redis_client

logger = logging.getLogger(__name__)

class CacheStatistics:
    def __init__(self):
        pass

    def record_hit(self, namespace: str, latency_ms: float):
        if not redis_client.is_available():
            return
        try:
            client = redis_client.get_client()
            client.hincrby(f"cache_stats:{namespace}", "hits", 1)
            client.hincrbyfloat(f"cache_stats:{namespace}", "total_latency", latency_ms)
            client.hincrby(f"cache_stats:{namespace}", "latency_count", 1)
        except Exception as e:
            logger.error(f"Failed to record cache hit: {e}")

    def record_miss(self, namespace: str):
        if not redis_client.is_available():
            return
        try:
            client = redis_client.get_client()
            client.hincrby(f"cache_stats:{namespace}", "misses", 1)
        except Exception as e:
            logger.error(f"Failed to record cache miss: {e}")

    def get_stats(self):
        if not redis_client.is_available():
            return {"status": "disconnected"}
        
        try:
            client = redis_client.get_client()
            stats = {"status": "connected", "namespaces": {}}
            
            namespaces = ["response", "embedding", "retrieval", "rerank", "evaluation", "session"]
            for ns in namespaces:
                data = client.hgetall(f"cache_stats:{ns}")
                hits = int(data.get("hits", 0))
                misses = int(data.get("misses", 0))
                total = hits + misses
                hit_rate = (hits / total * 100) if total > 0 else 0.0
                
                keys_count = len(client.keys(f"{ns}:*"))
                
                stats["namespaces"][ns] = {
                    "hits": hits,
                    "misses": misses,
                    "hit_rate": round(hit_rate, 2),
                    "keys_count": keys_count,
                    "enabled": True
                }
            return stats
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "message": str(e)}

cache_stats = CacheStatistics()
