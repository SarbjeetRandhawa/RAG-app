"""
Semantic Cache Layer
====================
Instead of exact-match hashing, this module stores the embedding vector
of each cached question. On new queries, the new embedding is compared
against all stored embeddings using cosine similarity. If the similarity
exceeds the configured threshold, the cached response is returned.

Flow:
  1. New query arrives -> generate embedding
  2. Compare embedding against in-memory index (backed by Redis)
  3. If max_similarity >= threshold -> return cached_key (cache HIT)
  4. Otherwise -> run pipeline, store response + embedding (cache MISS)
"""

import json
import logging
import math
import os

logger = logging.getLogger(__name__)

SEMANTIC_THRESHOLD = float(os.environ.get("SEMANTIC_CACHE_THRESHOLD", "0.92"))

# Redis key that stores the semantic index as a JSON hash
# {cache_key: {"question": "...", "embedding": [...]}}
SEMANTIC_INDEX_KEY = "semantic:response_index"


def _cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticCache:
    """
    In-memory semantic index backed by Redis.
    On startup the index is loaded from Redis so it survives server restarts.
    """

    def __init__(self):
        # {cache_key: {"question": str, "embedding": list[float]}}
        self._index: dict = {}

    def load_from_redis(self, redis_client):
        """Rebuild in-memory index from Redis on startup."""
        try:
            raw = redis_client.get(SEMANTIC_INDEX_KEY)
            if raw:
                self._index = json.loads(raw)
                logger.info(f"[SemanticCache] Loaded {len(self._index)} entries from Redis.")
        except Exception as e:
            logger.warning(f"[SemanticCache] Could not load index from Redis: {e}")

    def _persist(self, redis_client):
        """Persist the in-memory index back to Redis."""
        try:
            redis_client.set(SEMANTIC_INDEX_KEY, json.dumps(self._index))
        except Exception as e:
            logger.warning(f"[SemanticCache] Could not persist index: {e}")

    def store(self, cache_key: str, question: str, embedding: list, redis_client=None):
        """Store a question embedding under its cache key."""
        self._index[cache_key] = {"question": question, "embedding": embedding}
        if redis_client:
            self._persist(redis_client)
        logger.info(f"[SemanticCache] Stored embedding for key: {cache_key[:32]}...")

    def find_similar(self, query_embedding: list, threshold: float = None) -> str | None:
        """
        Search the index for the most semantically similar cached question.
        Returns the matching cache_key if similarity >= threshold, else None.
        """
        if not self._index:
            return None

        effective_threshold = threshold if threshold is not None else SEMANTIC_THRESHOLD
        best_key = None
        best_score = -1.0

        for cache_key, entry in self._index.items():
            stored_embedding = entry.get("embedding", [])
            if not stored_embedding:
                continue
            score = _cosine_similarity(query_embedding, stored_embedding)
            if score > best_score:
                best_score = score
                best_key = cache_key

        if best_score >= effective_threshold:
            logger.info(f"[SemanticCache] Semantic HIT (similarity={best_score:.4f}) for key: {best_key[:32]}...")
            return best_key
        else:
            logger.info(f"[SemanticCache] Semantic MISS (best similarity={best_score:.4f}, threshold={effective_threshold})")
            return None

    def remove(self, cache_key: str, redis_client=None):
        """Remove an entry from the index (e.g. when cache is cleared)."""
        self._index.pop(cache_key, None)
        if redis_client:
            self._persist(redis_client)

    def clear(self, redis_client=None):
        """Wipe the entire semantic index."""
        self._index.clear()
        if redis_client:
            try:
                redis_client.delete(SEMANTIC_INDEX_KEY)
            except Exception:
                pass

    def __len__(self):
        return len(self._index)


# Singleton instance shared across the application
semantic_cache = SemanticCache()
