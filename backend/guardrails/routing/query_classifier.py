from generation.groq import complete_with_groq

def classify_query(query: str) -> str:
    """
    Classifies a query into 'CHITCHAT', 'GENERAL_KNOWLEDGE', 'DIRECT', or 'COMPLEX'.
    Uses Groq Llama model for classification.
    """
    system_prompt = (
        "You are a fast query classifier for a RAG system.\n"
        "Classify the user's query into exactly ONE of the following categories:\n"
        "1. CHITCHAT: Casual conversation, greetings, pleasantries, e.g. 'hello', 'who are you', 'thanks'.\n"
        "2. GENERAL_KNOWLEDGE: Basic math, common facts, or simple queries that do not require searching a specialized knowledge base (e.g. 'what is 2+2', 'capital of France').\n"
        "3. DIRECT: Simple factual questions that require searching a knowledge base.\n"
        "4. COMPLEX: Multi-step, analytical, or reasoning questions requiring deep context.\n\n"
        "Output ONLY the category name (CHITCHAT, GENERAL_KNOWLEDGE, DIRECT, or COMPLEX). Do not add any extra text or punctuation."
    )
    
    try:
        # Use llama-3.1-8b-instant for fast classification
        category = complete_with_groq(
            system_prompt=system_prompt, 
            user_prompt=query, 
            max_tokens=10,
            temperature=0.0
        )
        category_cleaned = category.strip().upper()
        
        if category_cleaned in ["CHITCHAT", "GENERAL_KNOWLEDGE", "DIRECT", "COMPLEX"]:
            return category_cleaned
            
        return "COMPLEX" # Fallback if model outputs something unexpected
    except Exception as e:
        print(f"Classification error: {e}")
        return "COMPLEX" # Fallback to standard RAG on error
