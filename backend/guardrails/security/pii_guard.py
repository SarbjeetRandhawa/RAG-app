import re

class PIIGuard:
    def check_pii(self, text: str) -> tuple[bool, str]:
        """
        Checks for potential Personally Identifiable Information (PII).
        Returns (is_safe, reason).
        """
        if not text:
            return True, ""
            
        # Basic Email check
        if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text):
            return False, "PII detected: Email address found."
        
        # Basic SSN check
        if re.search(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b', text):
            return False, "PII detected: SSN-like sequence found."
            
        # Basic Phone number check
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):
            return False, "PII detected: Phone number sequence found."
            
        return True, ""
