import time
import logging
from qdrant_client import QdrantClient
from ingestion.embed import get_embeddings
from models.chunk import Chunk, RetrievedChunk
from models.reranker import rerank

class RetrieverService:
    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name

    def retrieve(self, query: str, top_k: int = 20) -> list[RetrievedChunk]:
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

        retrieved_chunks = []
        for hit in results.points:
            payload = hit.payload
            retrieved_chunks.append(
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
                    vector_score=hit.score,
                    rerank_score=0.0
                )
            )

        # rerank_start = time.time()
        # reranked_results = rerank(query, retrieved_chunks)
        # rerank_time = time.time() - rerank_start

        logging.info("=" * 80)
        logging.info("Retrieval Timing Metrics")
        logging.info("=" * 80)
        logging.info(f"Embedding Time     : {embed_time:.4f} s")
        logging.info(f"Qdrant Search Time : {qdrant_time:.4f} s")
        # logging.info(f"Reranker Time      : {rerank_time:.4f} s")
        logging.info("=" * 80)

        return retrieved_chunks
