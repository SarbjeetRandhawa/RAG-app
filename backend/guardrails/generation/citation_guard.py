import re

class CitationGuard:
    def check_citations(self, answer: str) -> tuple[bool, str]:
        """
        Checks if the answer contains citations in the expected format, 
        e.g., [1] or similar brackets.
        """
        if not answer:
            return True, ""
            
        # Look for [1], [2], etc.
        # This is a soft check, only warning if no citations at all
        # are found in a presumably factual response.
        if not re.search(r'\[\d+\]', answer):
            return False, "Answer does not contain formatted citations (e.g., [1])."
            
        return True, ""
