import os
import cohere
from models.chunk import RetrievedChunk
from dotenv import load_dotenv

load_dotenv()

_K = 60  # Standard RRF constant
co = cohere.Client(os.environ.get("COHERE_API_KEY"))

def rrf_fusion(vector_chunks: list[RetrievedChunk], bm25_chunks: list[RetrievedChunk], k: int = _K, top_n: int = 30) -> list[RetrievedChunk]:
    """Merge two ranked lists using Reciprocal Rank Fusion. Returns top_n unique chunks."""
    
    chunk_map = {}
    
    # Process vector chunks
    for rank, chunk in enumerate(vector_chunks, start=1):
        if chunk.chunk.chunk_id not in chunk_map:
            chunk_map[chunk.chunk.chunk_id] = chunk
        chunk_map[chunk.chunk.chunk_id].rrf_score += 1.0 / (k + rank)
        
    # Process BM25 chunks
    for rank, chunk in enumerate(bm25_chunks, start=1):
        if chunk.chunk.chunk_id not in chunk_map:
            chunk_map[chunk.chunk.chunk_id] = chunk
        else:
            # Update BM25 score if it was already added by vector search
            chunk_map[chunk.chunk.chunk_id].bm25_score = chunk.bm25_score
        chunk_map[chunk.chunk.chunk_id].rrf_score += 1.0 / (k + rank)
        
    # Sort descending by rrf_score
    fused = sorted(list(chunk_map.values()), key=lambda c: c.rrf_score, reverse=True)
    return fused[:top_n]

from cache.decorators import cache_result

@cache_result(namespace="rerank", ttl=43200)
def cohere_rerank(query: str, chunks: list[RetrievedChunk], top_n: int = 20) -> list[RetrievedChunk]:
    """Call Cohere rerank-english-v3.0 API. Sets rerank_score from Cohere relevance_score."""
    if not chunks:
        return []
        
    texts = [c.chunk.text for c in chunks]
    
    results = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=texts,
        top_n=top_n
    )
    
    reranked_chunks = []
    for hit in results.results:
        original_chunk = chunks[hit.index]
        original_chunk.rerank_score = hit.relevance_score
        reranked_chunks.append(original_chunk)
        
    return reranked_chunks