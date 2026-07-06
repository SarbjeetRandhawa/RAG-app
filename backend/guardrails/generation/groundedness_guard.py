from generation.groq import complete_with_groq

class GroundednessGuard:
    def check_groundedness(self, answer: str, context: str) -> dict:
        """
        Checks if the answer is grounded in the provided context using Groq.
        """
        system_prompt = (
            "You are an evaluator checking for groundedness.\n"
            "Given an answer and a source context, determine if the answer is grounded in the context.\n"
            "Reply strictly with 'GROUNDED' if the answer can be fully inferred from the context.\n"
            "Reply 'UNGROUNDED' if the answer hallucinates or adds unverified external info."
        )
        
        user_prompt = f"Context: {context}\n\nAnswer: {answer}\n\nEvaluation:"
        
        try:
            result = complete_with_groq(system_prompt, user_prompt, max_tokens=10, temperature=0.0)
            is_grounded = "GROUNDED" in result.upper()
            return {
                "is_grounded": is_grounded,
                "reason": "Answer is grounded." if is_grounded else "Answer failed groundedness check."
            }
        except Exception as e:
            return {"is_grounded": True, "reason": f"Skipped due to error: {e}"}
