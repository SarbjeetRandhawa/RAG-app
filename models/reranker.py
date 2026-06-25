# reranker.py

from sentence_transformers import CrossEncoder

reranker_model = CrossEncoder(
    "BAAI/bge-reranker-large"
)

def rerank(query, chunks):

    pairs = [[query, chunk] for chunk in chunks]

    scores = reranker_model.predict(pairs)

    results = []

    for chunk, score in zip(chunks, scores):

        results.append({
            "text": chunk,
            "score": float(score)
        })

    return sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )