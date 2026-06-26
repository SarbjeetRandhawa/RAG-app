def build_prompt(query, chunks):
    context = "\n\n".join(
        [
            f"""Source: {c['source']}
Page: {c['page']}
Section: {c['section']}

{c['text']}
"""
            for c in chunks
        ]
    )

    prompt = f"""
You are a helpful AI assistant.

Answer ONLY using the provided context.

If the answer cannot be found in the context, say:

"I couldn't find that information in the provided documents."

--------------------

Context:

{context}

--------------------

Question:

{query}

Answer:
"""

    return prompt