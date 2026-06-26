from dataclasses import dataclass

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
