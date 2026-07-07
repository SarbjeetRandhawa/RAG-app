import time
import logging
from qdrant_client import QdrantClient
from ingestion.embed import get_embeddings
from models.chunk import Chunk, RetrievedChunk
from models.reranker import rrf_fusion, cohere_rerank
from ingestion.bm25_index import load_bm25

class RetrieverService:
    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name
        self.bm25_index, self.bm25_chunk_ids = load_bm25()

    def retrieve(self, query: str, top_k: int = 30) -> list[RetrievedChunk]:
        # 1. Vector Search
        embed_start = time.time()
        query_embedding = get_embeddings([query], input_type="search_query")[0]
        embed_time = time.time() - embed_start

        qdrant_start = time.time()
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k
        )
        qdrant_time = time.time() - qdrant_start

        vector_chunks = []
        for hit in results.points:
            payload = hit.payload
            vector_chunks.append(
                RetrievedChunk(
                    chunk=Chunk(
                        chunk_id=payload["chunk_id"],
                        document_id=payload["document_id"],
                        page=payload["page"],
                        section=payload["section"],
                        source=payload["source"],
                        chunk_index=payload["chunk_index"],
                        token_count=payload.get("token_count", 0),
                        text=payload["text"]
                    ),
                    vector_score=hit.score
                )
            )

        # 2. BM25 Search
        bm25_time = 0.0
        bm25_chunks = []
        if self.bm25_index:
            bm25_start = time.time()
            tokenized_query = query.lower().split()
            # Get top_k scores directly instead of chunks to map to IDs
            bm25_scores = self.bm25_index.get_scores(tokenized_query)
            
            # Get top indices
            top_n_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
            
            top_chunk_ids = [self.bm25_chunk_ids[i] for i in top_n_indices]
            
            # Fetch payloads for top BM25 results from Qdrant by chunk_id if needed, but they might already be in vector_chunks
            # Let's fetch the missing ones
            missing_ids = [cid for cid in top_chunk_ids if cid not in [vc.chunk.chunk_id for vc in vector_chunks]]
            
            if missing_ids:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                bm25_results = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=Filter(
                        should=[
                            FieldCondition(key="chunk_id", match=MatchValue(value=cid)) for cid in missing_ids
                        ]
                    ),
                    with_payload=True,
                    with_vectors=False,
                    limit=len(missing_ids)
                )[0]
                
                # Create a map for fast lookup
                payload_map = {res.payload["chunk_id"]: res.payload for res in bm25_results}
            else:
                payload_map = {}
                
            # Create retrieved chunks for BM25
            for idx in top_n_indices:
                cid = self.bm25_chunk_ids[idx]
                score = bm25_scores[idx]
                
                # Check if it was in vector search results to reuse the payload
                vector_match = next((vc for vc in vector_chunks if vc.chunk.chunk_id == cid), None)
                
                if vector_match:
                    payload = {
                        "chunk_id": vector_match.chunk.chunk_id,
                        "document_id": vector_match.chunk.document_id,
                        "page": vector_match.chunk.page,
                        "section": vector_match.chunk.section,
                        "source": vector_match.chunk.source,
                        "chunk_index": vector_match.chunk.chunk_index,
                        "token_count": vector_match.chunk.token_count,
                        "text": vector_match.chunk.text
                    }
                elif cid in payload_map:
                    payload = payload_map[cid]
                else:
                    continue
                    
                bm25_chunks.append(
                    RetrievedChunk(
                        chunk=Chunk(
                            chunk_id=payload["chunk_id"],
                            document_id=payload["document_id"],
                            page=payload["page"],
                            section=payload["section"],
                            source=payload["source"],
                            chunk_index=payload["chunk_index"],
                            token_count=payload.get("token_count", 0),
                            text=payload["text"]
                        ),
                        vector_score=0.0,
                        bm25_score=score
                    )
                )
            bm25_time = time.time() - bm25_start

        # 3. RRF Fusion
        rrf_start = time.time()
        fused_chunks = rrf_fusion(vector_chunks, bm25_chunks, top_n=top_k)
        rrf_time = time.time() - rrf_start
        
        # 4. Cohere Rerank
        rerank_start = time.time()
        final_chunks = cohere_rerank(query, fused_chunks, top_n=10)
        rerank_time = time.time() - rerank_start

        logging.info("=" * 80)
        logging.info("Retrieval Timing Metrics")
        logging.info("=" * 80)
        logging.info(f"Embedding Time     : {embed_time:.4f} s")
        logging.info(f"Qdrant Search Time : {qdrant_time:.4f} s")
        logging.info(f"BM25 Search Time   : {bm25_time:.4f} s")
        logging.info(f"RRF Fusion Time    : {rrf_time:.4f} s")
        logging.info(f"Cohere Rerank Time : {rerank_time:.4f} s")
        logging.info("=" * 80)

        return final_chunks
