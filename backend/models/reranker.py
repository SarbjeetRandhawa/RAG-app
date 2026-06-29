# reranker.py

from sentence_transformers import CrossEncoder
from models.chunk import RetrievedChunk

reranker_model = CrossEncoder(
    "BAAI/bge-reranker-base"
)

def rerank(query: str, retrieved_chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    if not retrieved_chunks:
        return []

    pairs = [[query, rc.chunk.text] for rc in retrieved_chunks]

    scores = reranker_model.predict(pairs)

    for rc, score in zip(retrieved_chunks, scores):
        rc.rerank_score = float(score)

    return sorted(
        retrieved_chunks,
        key=lambda x: x.rerank_score,
        reverse=True
    )