from ingestion.extract import extract_text
from ingestion.clean import clean_text
from ingestion.chunk import chunk_text
from ingestion.embed import get_embeddings
from models.reranker import rerank

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

PDF_PATH = "data/data.pdf"

COLLECTION_NAME = "documents_v3"


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

    pages_data = extract_text(PDF_PATH)

    pages_data = clean_text(pages_data)

    chunks_data = chunk_text(pages_data)

    embeddings = get_embeddings(chunks_data)

    points = []

    for index, (chunk, embedding) in enumerate(
        zip(chunks_data, embeddings)
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
        limit=20
    )

    # print("\nQdrant Results Before Reranking\n")

    # for i, hit in enumerate(results.points[:10]):
    #     print("=" * 80)
    #     print(f"Rank: {i+1}")
    #     print(f"Qdrant Score: {hit.score:.4f}")
    #     print(hit.payload["text"][:200])
    #     print()

    chunks = [hit.payload["text"] for hit in results.points]

    reranked_results = rerank(query, chunks)

    print("\nResults\n")

    # Display the top 5 reranked results
    for res in reranked_results[:5]:

        print("=" * 80)

        print(
            f"Score: {res['score']:.4f}"
        )

        print()

        print(
            res["text"]
        )

        print()


if __name__ == "__main__":

    create_collection()

    ingest_document()

    while True:
        search()