from dataclasses import dataclass
import re

@dataclass
class InputGuardResult:
    is_valid: bool
    message: str | None = None

class InputGuard:
    MAX_QUERY_LENGTH = 2000

    def validate(self, query: str) -> InputGuardResult:
        if not isinstance(query, str):
            return InputGuardResult(False, "Query must be a string.")

        query = query.strip()

        if not query:
            return InputGuardResult(
                False,
                "Please enter a question."
            )

        if len(query) > self.MAX_QUERY_LENGTH:
            return InputGuardResult(
                False,
                "Your question is too long."
            )

        if self._looks_like_gibberish(query):
            return InputGuardResult(
                False,
                "I couldn't understand your question."
            )

        return InputGuardResult(True)
    
    def _looks_like_gibberish(self, text: str):
        text = text.lower()

        if re.fullmatch(r"[a-z]{12,}", text):
            return True

        vowels = sum(c in "aeiou" for c in text if c.isalpha())
        letters = sum(c.isalpha() for c in text)

        if letters > 8 and vowels / letters < 0.15:
            return True

        return False
