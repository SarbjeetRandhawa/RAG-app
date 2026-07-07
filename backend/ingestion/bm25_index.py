import os
import pickle
import logging
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BM25_INDEX_PATH = "data/bm25_index.pkl"

def build_and_save_bm25(client: QdrantClient, collection_name: str, save_path: str = BM25_INDEX_PATH):
    """
    Scrolls through all chunks in Qdrant, tokenizes their text, builds a BM25 index,
    and saves the (index, chunk_ids) tuple to disk.
    """
    logging.info("Starting BM25 index build...")
    
    # Scroll all points to get payloads
    all_payloads = []
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=collection_name,
            with_payload=True,
            with_vectors=False,
            limit=1000,
            offset=offset
        )
        all_payloads.extend([r.payload for r in records])
        if offset is None:
            break

    if not all_payloads:
        logging.warning("No chunks found in Qdrant to build BM25 index.")
        return

    # Extract texts and chunk_ids
    texts = [payload["text"] for payload in all_payloads]
    chunk_ids = [payload["chunk_id"] for payload in all_payloads]
    
    # Tokenize texts (simple whitespace splitting for now)
    tokenized_corpus = [text.lower().split() for text in texts]
    
    logging.info(f"Building BM25Okapi with {len(tokenized_corpus)} chunks...")
    bm25 = BM25Okapi(tokenized_corpus)
    
    data_to_save = {
        "bm25": bm25,
        "chunk_ids": chunk_ids
    }

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(data_to_save, f)
        
    logging.info(f"BM25 index saved successfully to {save_path}.")

def load_bm25(save_path: str = BM25_INDEX_PATH) -> tuple[BM25Okapi | None, list[str]]:
    """Loads the BM25 index and corresponding chunk IDs from disk."""
    if not os.path.exists(save_path):
        logging.warning(f"BM25 index not found at {save_path}.")
        return None, []
        
    with open(save_path, "rb") as f:
        data = pickle.load(f)
        
    return data.get("bm25"), data.get("chunk_ids", [])
