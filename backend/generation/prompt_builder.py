class PromptBuilder:
    def build(self, query, chunks):
        context = "\n\n".join(
            f"""Source: {chunk.source}
Page: {chunk.page}
Section: {chunk.section}

{chunk.text}
"""
            for chunk in chunks
        )

        prompt = f"""
Context:

{context}

--------------------

Question:

{query}

Answer:
"""

        return prompt