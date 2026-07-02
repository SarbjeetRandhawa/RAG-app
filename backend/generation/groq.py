import os
from openai import OpenAI
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BACKEND_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH, override=True)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_QUERY_REWRITE_MODEL = os.environ.get(
    "GROQ_QUERY_REWRITE_MODEL",
    "llama-3.1-8b-instant"
)

_client = None


def get_groq_client():
    global _client
    if _client is None:
        api_key = (os.environ.get("GROQ_API_KEY") or "").strip().strip('"').strip("'")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        _client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
    return _client


def complete_with_groq(
    system_prompt: str,
    user_prompt: str,
    model: str = GROQ_QUERY_REWRITE_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 160
) -> str:
    response = get_groq_client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()
