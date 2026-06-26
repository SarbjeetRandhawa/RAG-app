import uuid
from ingestion.extract import extract_text
from ingestion.clean import clean_text
from ingestion.chunk import chunk_text
from ingestion.embed import get_embeddings
from models.reranker import rerank
from models.chunk import Chunk
from generation.prompt_builder import build_prompt
from generation.llm import generate_answer

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

PDF_PATH = "data/data.pdf"

COLLECTION_NAME = "documents_v4"  # v4: switched to BAAI/bge-large-en-v1.5 (1024-dim)


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


def ingest_document():

    pages_data = extract_text(PDF_PATH)

    pages_data = clean_text(pages_data)

    chunks_data = chunk_text(pages_data)

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

    print(
        f"Inserted {len(points)} chunks"
    )


def search():

    query = input(
        "\nAsk a question: "
    )

    query_embedding = get_embeddings([query])[0]

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=20
    )

    retrieved_chunks = []
    for hit in results.points:
        payload = hit.payload
        retrieved_chunks.append(
            Chunk(
                chunk_id=payload["chunk_id"],
                document_id=payload["document_id"],
                page=payload["page"],
                section=payload["section"],
                source=payload["source"],
                chunk_index=payload["chunk_index"],
                token_count=payload.get("token_count", 0),
                text=payload["text"]
            )
        )

    reranked_results = rerank(query, retrieved_chunks)

    # ── Display top-5 reranked context chunks ──────────────────────────────
    print("\nTop Reranked Chunks\n")
    for chunk in reranked_results[:5]:
        print("=" * 80)
        print(f"Score: {chunk.score:.4f}")
        print(f"Doc: {chunk.document_id} | Page: {chunk.page} | Section: {chunk.section} | Tokens: {chunk.token_count}")
        print()
        print(chunk.text)
        print()

    # ── Generation ─────────────────────────────────────────────────────────
    top_chunks = [
        {
            "source": c.document_id,
            "page": c.page,
            "section": c.section,
            "text": c.text,
        }
        for c in reranked_results[:3]  # feed top-3 chunks to the LLM
    ]

    prompt = build_prompt(query, top_chunks)
    print("Generating answer...\n")
    answer = generate_answer(prompt)

    print("=" * 80)
    print("Answer")
    print("=" * 80)
    print(answer)
    print()


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
        print("\nIngestion complete. Restart the app to search.")

    elif choice == "2":
        print("\nSkipping ingestion — using existing Qdrant data.\n")
        while True:
            search()

    elif choice == "3":
        ingest_document()
        print("\nIngestion complete. Starting search...\n")
        while True:
            search()

    elif choice == "q":
        print("Bye!")

    else:
        print("Invalid choice. Please restart and pick 1, 2, 3, or q.")
