import logging
from typing import List, Any

from generation.groq import complete_with_groq
from .prompt import REFLECTION_SYSTEM_PROMPT, REFLECTION_USER_INSTRUCTIONS


class Reflector:
    """Responsible for reviewing and improving a draft answer using retrieved chunks.

    Usage:
        reflector = Reflector()
        final = reflector.reflect(question, retrieved_chunks, draft_answer)
    """

    def __init__(self, enabled: bool = True, model: str | None = None):
        self.enabled = enabled
        self.model = model

    def _format_chunks(self, retrieved_chunks: List[Any]) -> str:
        lines = []
        for i, rc in enumerate(retrieved_chunks, start=1):
            # support either a raw chunk object or a reranked wrapper with .chunk
            chunk = getattr(rc, "chunk", rc)
            meta = []
            source = getattr(chunk, "source", None) or getattr(chunk, "fileName", "unknown")
            page = getattr(chunk, "page", None)
            chunk_id = getattr(chunk, "chunk_id", None) or getattr(chunk, "id", None)
            section = getattr(chunk, "section", None)
            text = getattr(chunk, "text", getattr(chunk, "content", ""))

            meta.append(f"source={source}")
            if page is not None:
                meta.append(f"page={page}")
            if section:
                meta.append(f"section={section}")
            if chunk_id:
                meta.append(f"chunk_id={chunk_id}")

            header = f"--- CHUNK {i} ({', '.join(meta)}) ---"
            lines.append(header)
            lines.append(text)
            lines.append("")

        return "\n".join(lines)

    def reflect(self, question: str, retrieved_chunks: List[Any], draft_answer: str, temperature: float = 0.0) -> str:
        """Run reflection to produce a final answer.

        Returns the final improved answer string. If reflection is disabled, returns draft_answer.
        """
        if not self.enabled:
            logging.debug("Reflection is disabled; returning draft answer.")
            return draft_answer

        try:
            chunks_text = self._format_chunks(retrieved_chunks)
            user_prompt = REFLECTION_USER_INSTRUCTIONS.format(
                question=question,
                draft=draft_answer,
                chunks=chunks_text,
            )

            logging.info("Running reflection LLM call to improve draft answer via Groq.")
            final = complete_with_groq(REFLECTION_SYSTEM_PROMPT, user_prompt, temperature=temperature)

            # The contract: LLM returns only the final improved answer.
            return final.strip()

        except Exception as e:
            logging.exception("Reflection failed: %s", e)
            # On failure, fall back to draft answer (safe behavior)
            return draft_answer
