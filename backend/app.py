import uuid
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
from ingestion.extract import extract_text
from ingestion.clean import clean_text
from ingestion.chunk import chunk_text
from ingestion.embed import get_embeddings
from models.reranker import rerank
from models.chunk import Chunk, RetrievedChunk
from retrieval.retriever import RetrieverService
from generation.generator import GenerationService
from pipeline.runner import run_chat_pipeline


from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

PDF_PATH = "data/data.pdf"

COLLECTION_NAME = "documents_v1"  # v4: switched to BAAI/bge-large-en-v1.5 (1024-dim)
MAX_CONTEXT_TOKENS = 6000


client = QdrantClient(
    host="localhost",
    port=6333
)


def create_collection():

    collections = client.get_collections()

    names = [
        c.name
        for c in collections.collections
    ]

    if COLLECTION_NAME in names:
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1024,           # BAAI/bge-large-en-v1.5 output dimension
            distance=Distance.COSINE
        )
    )


def ingest_document(pdf_path=PDF_PATH, document_id="data", filename="data.pdf"):

    pages_data = extract_text(pdf_path)

    pages_data = clean_text(pages_data)

    chunks_data = chunk_text(pages_data)

    for chunk in chunks_data:
        chunk.document_id = document_id
        chunk.source = filename
        chunk.chunk_id = f"{document_id}_{chunk.chunk_index}"

    embeddings = get_embeddings([chunk.text for chunk in chunks_data])

    points = []

    for index, (chunk, embedding) in enumerate(
        zip(chunks_data, embeddings)
    ):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))

        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "page": chunk.page,
                    "section": chunk.section,
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    logging.info(
        f"Inserted {len(points)} chunks"
    )
    return chunks_data


def search():

    query = input(
        "\nAsk a question: "
    )

    result = run_chat_pipeline(query, client, COLLECTION_NAME, MAX_CONTEXT_TOKENS)

    logging.info("\nTop Reranked Chunks\n")
    for rc in result["reranked_results"][:5]:
        logging.info("=" * 80)
        logging.info(f"Vector Score: {rc.vector_score:.4f} | Rerank Score: {rc.rerank_score:.4f}")
        logging.info(f"Doc: {rc.chunk.document_id} | Page: {rc.chunk.page} | Section: {rc.chunk.section} | Tokens: {rc.chunk.token_count}")
        logging.info("\n" + rc.chunk.text + "\n")

    print("=" * 80)
    print("Answer")
    print("=" * 80)
    print(result["answer"])
    print()

    logging.info("=" * 80)
    logging.info("Total Timing Metrics")
    logging.info("=" * 80)
    logging.info(f"Total Time         : {result['total_time']:.4f} s")
    logging.info("=" * 80)



def main_menu():

    print("\n" + "=" * 50)
    print("       RAG Pipeline — What do you want to do?")
    print("=" * 50)
    print("  [1] Ingest document  (embed & store in Qdrant)")
    print("  [2] Search & Generate (query + LLM answer)")
    print("  [3] Ingest then Search & Generate")
    print("  [q] Quit")
    print("=" * 50)

    choice = input("Enter choice: ").strip().lower()

    return choice


if __name__ == "__main__":

    create_collection()

    choice = main_menu()

    if choice == "1":
        ingest_document()
        logging.info("\nIngestion complete. Restart the app to search.")

    elif choice == "2":
        logging.info("\nSkipping ingestion — using existing Qdrant data.\n")
        while True:
            search()

    elif choice == "3":
        ingest_document()
        logging.info("\nIngestion complete. Starting search...\n")
        while True:
            search()

    elif choice == "q":
        logging.info("Bye!")

    else:
        logging.warning("Invalid choice. Please restart and pick 1, 2, 3, or q.")
