def filter_relevant_chunks(reranked_results: list, threshold: float = 0.3) -> list:
    """
    Filters out chunks that fall below the relevance threshold.
    This ensures the LLM only sees high-quality context.
    """
    if not reranked_results:
        return []
        
    return [result for result in reranked_results if result.rerank_score >= threshold]
