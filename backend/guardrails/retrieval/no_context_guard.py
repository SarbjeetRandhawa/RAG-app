def check_no_context(reranked_results: list, threshold: float = 0.1) -> bool:
    """
    Checks if the highest reranker score is below the threshold.
    Returns True if NO CONTEXT is found (triggering the guardrail).
    """
    if not reranked_results:
        return True # No results at all
        
    # Assuming reranked_results is sorted descending by rerank_score
    top_score = reranked_results[0].rerank_score
    
    # If the best score is lower than our strict threshold, we lack context.
    return top_score < threshold
