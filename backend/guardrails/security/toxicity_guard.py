from generation.groq import complete_with_groq

class ToxicityGuard:
    def check_toxicity(self, text: str) -> tuple[bool, str]:
        """
        Uses an LLM to check if the text contains toxicity, abusive language,
        hate speech, violent requests, illegal activity, or explicit sexual content.
        Returns (is_safe, reason).
        """
        if not text:
            return True, ""
            
        # Basic keyword checks for very obvious violations
        text_lower = text.lower()
        banned_keywords = ["bomb", "terror", "kill", "murder", "suicide", "hack", "illegal", "drugs", "meth", "cocaine"]
        if any(word in text_lower for word in banned_keywords):
            return False, "Input flagged by keyword safety filter."
            
        system_prompt = (
            "You are a strict safety classifier.\n"
            "Analyze the user's input and determine if it contains any of the following:\n"
            "1. Abusive language or hate speech\n"
            "2. Violent requests\n"
            "3. Illegal activity requests\n"
            "4. Explicit sexual content\n\n"
            "Output 'SAFE' if none of these are present.\n"
            "Output 'UNSAFE' if any of these are present."
        )
        
        user_prompt = f"Input to classify:\n{text}\n\nClassification:"
        
        try:
            result = complete_with_groq(
                system_prompt=system_prompt, 
                user_prompt=user_prompt, 
                max_tokens=10,
                temperature=0.0
            )
            
            is_safe = "UNSAFE" not in result.upper()
            if not is_safe:
                return False, "Input flagged for inappropriate content (toxicity, hate speech, etc.)."
            return True, ""
        except Exception as e:
            error_str = str(e).lower()
            # If the API explicitly blocks the request due to its own moderation policies or throws *any* error for a highly controversial prompt
            if "flagged" in error_str or "policy" in error_str or "moderation" in error_str or "400" in error_str or "bad request" in error_str:
                return False, "Input flagged by safety systems."
            
            # On other errors (like timeout), default to safe to not break pipeline availability
            print(f"Toxicity guard API error: {e}")
            return True, ""
