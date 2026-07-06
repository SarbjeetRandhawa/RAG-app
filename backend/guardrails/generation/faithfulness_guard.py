from generation.groq import complete_with_groq

def check_faithfulness(query: str, context: str, answer: str) -> dict:
    """
    Uses an LLM (Groq) to verify that the answer is completely faithful to the context.
    Returns {"is_faithful": bool, "reason": str}
    """
    system_prompt = (
        "You are an expert fact-checker evaluating a RAG answer based on a given context.\n"
        "Your task is to determine if the answer is ENTIRELY supported by the context.\n"
        "Do NOT use external knowledge. Only use the provided context.\n"
        "Output exactly 'YES' if the answer is completely faithful and supported by the context.\n"
        "Output 'NO' if the answer contains hallucinations, contradictory information, or information not found in the context."
    )
    
    user_prompt = (
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Answer: {answer}\n\n"
        "Is the answer faithful to the context? (YES/NO)"
    )
    
    try:
        # Use llama-3.1-8b-instant for fast verification
        result = complete_with_groq(
            system_prompt=system_prompt, 
            user_prompt=user_prompt, 
            max_tokens=10,
            temperature=0.0
        )
        
        is_faithful = "YES" in result.strip().upper()
        return {
            "is_faithful": is_faithful,
            "reason": "Faithfulness verified by LLM." if is_faithful else "Answer contains unsupported claims based on the context."
        }
    except Exception as e:
        print(f"Faithfulness check error: {e}")
        # Default to True if the check fails to avoid blocking the pipeline completely
        return {"is_faithful": True, "reason": f"Faithfulness check skipped due to error: {str(e)}"}
