from dataclasses import dataclass
from typing import Optional
from models.graph import GraphDocument

@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    page: int
    section: str
    source: str
    chunk_index: int
    token_count: int
    text: str
    score: float = 0.0

@dataclass
class ProcessedChunk:
    chunk: Chunk
    graph_document: Optional[GraphDocument] = None

@dataclass
class RetrievedChunk:
    chunk: Chunk
    vector_score: float = 0.0
    rerank_score: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0
