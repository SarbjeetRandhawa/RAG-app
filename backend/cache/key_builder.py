import hashlib
import json
import re

def _hash(text: str) -> str:
    """Generate a SHA-256 hash for the given text to create a compact, unique cache key."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# Stop words to strip before normalization (keeps semantically meaningful tokens)
_STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "of", "to", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "about"
}

def _normalize_query(query: str) -> str:
    """
    Normalize a query for cache key generation.
    - Lowercase
    - Remove punctuation
    - Remove stop words
    - Sort remaining tokens alphabetically

    This ensures minor LLM rewrite variations (word order, capitalization,
    extra filler words) still resolve to the same cache key.

    Examples:
      "How many leaves per year?"          -> "leaves many year"
      "how many annual leaves"             -> "annual leaves many"
      "What is the leave entitlement?"     -> "entitlement leave"
    """
    tokens = re.findall(r'\b\w+\b', query.lower())
    tokens = [t for t in tokens if t not in _STOP_WORDS]
    tokens.sort()
    return " ".join(tokens)

def build_response_key(question: str, model: str, memory: dict = None) -> str:
    """Generate a cache key for final LLM responses based on the question and model."""
    # NOTE: memory is intentionally excluded from the key.
    # Including memory causes the same question to always produce a different hash
    # because memory accumulates over time, resulting in perpetual cache misses.
    return f"response:{_hash(question + model)}"

def build_embedding_key(text: str) -> str:
    """Generate a cache key for text embeddings."""
    return f"embedding:{_hash(text)}"

def build_retrieval_key(query: str) -> str:
    """Generate a cache key for document retrieval queries."""
    # Normalize so minor LLM-rewrite variations still map to the same key
    return f"retrieval:{_hash(_normalize_query(query))}"

def build_rerank_key(query: str) -> str:
    """Generate a cache key for reranking results based on the query."""
    # Normalize so minor LLM-rewrite variations still map to the same key
    return f"rerank:{_hash(_normalize_query(query))}"

def build_evaluation_key(question: str, answer: str) -> str:
    """Generate a cache key for answer evaluations."""
    return f"evaluation:{_hash(question + answer)}"

def build_session_key(session_id: str) -> str:
    """Generate a cache key for storing session state."""
    return f"session:{session_id}"
