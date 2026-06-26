# reranker.py

from sentence_transformers import CrossEncoder
from models.chunk import Chunk

reranker_model = CrossEncoder(
    "BAAI/bge-reranker-large"
)

def rerank(query: str, chunks: list[Chunk]) -> list[Chunk]:
    if not chunks:
        return []

    pairs = [[query, chunk.text] for chunk in chunks]

    scores = reranker_model.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk.score = float(score)

    return sorted(
        chunks,
        key=lambda x: x.score,
        reverse=True
    )