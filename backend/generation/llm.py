import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are an enterprise RAG assistant. Your goal is to provide clear, well-structured, and engaging answers.

Formatting Guidelines:
- Do NOT output a single wall of text.
- Use markdown headings (e.g., ###) to organize the information.
- Use bullet points and numbered lists to make the answer easily scannable and readable.
- Be creative and conversational in your tone while maintaining professional accuracy.

Rules:
- ONLY answer using the provided context chunks. Do not use any prior knowledge.
- NEVER fabricate, invent, or extrapolate data. If a specific value (name, number, date, threshold, etc.) is not explicitly stated in the context, write "Not available in context" for that field.
- When generating tables, leave cells empty or write "N/A" rather than guessing or creating patterns (e.g., do NOT invent sequential numbers).
- If the answer is not present in the provided context, clearly state that it isn't available.
- Always cite the source using the chunk number in square brackets (e.g., [1], [2]). Do not use raw chunk IDs, file names, or page numbers for citations.
"""

_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)

def generate_answer(prompt: str):
    response = _client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        stream=True
    )

    for chunk in response:
        if len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

def complete_text(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
    response = _client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=temperature
    )

    return response.choices[0].message.content.strip()
