class PromptBuilder:
    def build(self, query, chunks, memory_context=None):
        context = "\n\n".join(
            f"""Source: {chunk.source}
Page: {chunk.page}
Section: {chunk.section}

{chunk.text}
"""
            for chunk in chunks
        )
        memory_context = memory_context or {}
        memory_summary = memory_context.get("summary") or "None"
        recent_messages = memory_context.get("recent_messages_text") or "None"

        prompt = f"""
Conversation Memory:

Summary of older messages:
{memory_summary}

Recent messages:
{recent_messages}

--------------------

Context:

{context}

--------------------

Question:

{query}

Answer:
"""

        return prompt
