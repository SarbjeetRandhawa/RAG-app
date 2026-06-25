from ingestion.extract import extract_text
from ingestion.clean import clean_text
from ingestion.chunk import chunk_text
from ingestion.embed import get_embeddings

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

PDF_PATH = "data/data.pdf"

COLLECTION_NAME = "documents_v2"


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
            size=384,
            distance=Distance.COSINE
        )
    )


def ingest_document():

    text = extract_text(PDF_PATH)

    text = clean_text(text)

    chunks = chunk_text(text)

    embeddings = get_embeddings(chunks)

    points = []

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):

    
        points.append(
        PointStruct(
            id=index,
            vector=embedding,
            payload={
                "text": chunk
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
        limit=5
    )

    print("\nResults\n")

    for hit in results.points:

        print("=" * 80)

        print(
            f"Score: {hit.score:.4f}"
        )

        print()

        print(
            hit.payload["text"]
        )

        print()


if __name__ == "__main__":

    create_collection()

    ingest_document()

    while True:
        search()