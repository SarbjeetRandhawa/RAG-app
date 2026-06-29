import logging
from sentence_transformers import SentenceTransformer

logging.info("Step 1: Loading model")

# BAAI/bge-large-en-v1.5 — 1024-dim, production-grade, top MTEB rankings
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

logging.info("Step 2: Model loaded")


def get_embeddings(chunks):

    logging.info(f"Creating embeddings for {len(chunks)} chunks")

    return model.encode(
        chunks,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True
    ).tolist()


