# reranker.py  –  RRF Passthrough reranker
# Computes Reciprocal Rank Fusion score from the vector-search rank position.
# Formula: rrf_score = 1 / (k + rank)  where k=60 (standard RRF constant).
# Lower rrf_score = lower rank (worse) → sorted ascending gives best chunks first.
# No API call, no extra latency (<1 ms).

from models.chunk import RetrievedChunk

_K = 60  # Standard RRF constant


def rerank(query: str, retrieved_chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """RRF passthrough reranker: scores chunks by retrieval rank, no API call."""
    if not retrieved_chunks:
        return []

    # Assign RRF scores based on position in vector-search result list
    # rank is 1-indexed; higher rank (rank=1) → highest rrf_score = 1/(60+1)
    candidates = []
    for rank, rc in enumerate(retrieved_chunks, start=1):
        rc.rrf_score = 1.0 / (_K + rank)
        rc.rerank_score = rc.rrf_score  # keep rerank_score in sync
        candidates.append(rc)

    # Sort descending by rrf_score so best chunks come first, take top 10
    top = sorted(candidates, key=lambda c: c.rrf_score, reverse=True)[:10]
    return top