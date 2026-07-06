class PromptInjectionGuard:
    def check_injection(self, text: str) -> tuple[bool, str]:
        """
        Checks for common prompt injection patterns.
        Returns (is_safe, reason).
        """
        if not text:
            return True, ""
            
        injection_phrases = [
            "ignore previous",
            "ignore all previous",
            "forget previous",
            "system prompt",
            "you are now",
            "disregard rules",
            "bypassing restrictions",
            "do anything now"
        ]
        
        text_lower = text.lower()
        for phrase in injection_phrases:
            if phrase in text_lower:
                return False, f"Potential prompt injection detected (pattern match: {phrase})."
                
        return True, ""
