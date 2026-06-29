# reranker.py

import os
import cohere
from dotenv import load_dotenv
from models.chunk import RetrievedChunk

load_dotenv()

co = cohere.Client(os.environ.get("COHERE_API_KEY"))

def rerank(query: str, retrieved_chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    if not retrieved_chunks:
        return []

    docs = [rc.chunk.text for rc in retrieved_chunks]

    response = co.rerank(
        model='rerank-english-v3.0',
        query=query,
        documents=docs,
        top_n=len(docs)
    )

    reranked_chunks = []
    for result in response.results:
        rc = retrieved_chunks[result.index]
        rc.rerank_score = float(result.relevance_score)
        reranked_chunks.append(rc)

    return reranked_chunks
