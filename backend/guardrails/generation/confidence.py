_RRF_MAX = 1.0 / (60 + 1)   # Maximum possible RRF score (rank-1 result)


def calculate_confidence(reranked_results: list, filtered_results: list) -> dict:
    """
    Calculates a confidence score based on the reranker scores.
    Normalises RRF scores against the theoretical maximum so the
    final confidence is expressed on a 0–1 scale.
    """
    if not reranked_results or not filtered_results:
        return {"score": 0.0, "level": "Low"}

    top_score = filtered_results[0].rerank_score

    # Normalise: best possible chunk (rank-1) → 1.0, lower ranks → proportionally less
    top_norm = min(top_score / _RRF_MAX, 1.0)

    avg_raw = sum(r.rerank_score for r in filtered_results) / len(filtered_results)
    avg_norm = min(avg_raw / _RRF_MAX, 1.0)

    # Weight top match heavily, give some credit for having multiple good matches
    confidence_score = (top_norm * 0.7) + (avg_norm * 0.3)

    # Cap at 1.0 just in case
    confidence_score = min(1.0, confidence_score)

    if confidence_score >= 0.75:
        level = "High"
    elif confidence_score >= 0.4:
        level = "Medium"
    else:
        level = "Low"

    return {
        "score": float(f"{confidence_score:.2f}"),
        "level": level
    }
