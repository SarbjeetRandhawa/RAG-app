class PromptBuilder:
    def build(self, query, chunks, memory_context=None):
        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            context_parts.append(f"--- CHUNK {i} ---\nSource: {chunk.source}\nPage: {chunk.page}\nSection: {chunk.section}\n\n{chunk.text}")
        context = "\n\n".join(context_parts)
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
