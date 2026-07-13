import functools
from cache.cache_manager import cache_manager
from cache.key_builder import (
    build_embedding_key, 
    build_retrieval_key, 
    build_rerank_key, 
    build_evaluation_key
)

def cache_result(namespace: str, ttl: int = None):
    """
    A decorator to cache the results of a function execution in Redis.
    
    Args:
        namespace (str): The namespace for this cache (e.g., 'embedding', 'retrieval', 'rerank').
                         This helps separate and toggle caching for different parts of the pipeline.
        ttl (int, optional): Time-to-live in seconds. Determines how long the item stays in cache.
    
    Returns:
        The result of the wrapped function, either fetched from cache (on hit) 
        or executed and newly stored in cache (on miss).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_manager.is_enabled(namespace):
                return func(*args, **kwargs)
                
            key = None
            if namespace == "embedding":
                texts = kwargs.get('texts') if 'texts' in kwargs else args[0]
                if texts and isinstance(texts, list):
                    text = texts[0]
                    key = build_embedding_key(text)
            elif namespace == "retrieval":
                query = kwargs.get('query') if 'query' in kwargs else (args[1] if len(args)>1 else "")
                key = build_retrieval_key(query)
            elif namespace == "rerank":
                query = kwargs.get('query') if 'query' in kwargs else (args[0] if len(args)>0 else "")
                key = build_rerank_key(query)
            elif namespace == "evaluation":
                payload = kwargs.get('eval_payload') if 'eval_payload' in kwargs else (args[1] if len(args)>1 else {})
                question = payload.get("question", "")
                answer = payload.get("answer", "")
                key = build_evaluation_key(question, answer)
            
            if not key:
                return func(*args, **kwargs)

            cached_result = cache_manager.get(key, namespace)
            if cached_result is not None:
                return cached_result
                
            result = func(*args, **kwargs)
            
            if result is not None:
                cache_manager.set(key, result, namespace, ttl)
                
            return result
        return wrapper
    return decorator
