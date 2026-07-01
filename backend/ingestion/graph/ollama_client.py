import json
import logging
import time
from typing import Tuple

from openai import OpenAI
from models.graph import RawGraphExtraction

SYSTEM_PROMPT = """/no_think
You are an expert NLP graph extraction system.
Extract entities and relationships from the provided text.

Entity Types (pick one): PERSON, ORGANIZATION, LOCATION, CONCEPT, EVENT, PRODUCT

Preferred Relationship Types (use these if possible):
CREATED, WORKS_FOR, LOCATED_IN, PART_OF, MEMBER_OF, USES, DEPENDS_ON, REFERENCES, OWNS, RELATED_TO

Rules:
1. Only extract information explicitly present in the text.
2. For entities: provide 'name' exactly as it appears, and 'type'.
3. For relationships: 'source_entity_name' and 'target_entity_name' must exactly match entity names.
4. Provide 'relationship_type', 'confidence' (0.0-1.0), and 'evidence' (exact substring from text).
5. Do not hallucinate. Return empty lists if nothing is found.

Return ONLY valid JSON in this exact format, no explanation:
{
  "entities": [{"name": "...", "type": "..."}],
  "relationships": [{"source_entity_name": "...", "target_entity_name": "...", "relationship_type": "...", "confidence": 0.9, "evidence": "..."}]
}"""

class OllamaGraphClient:
    def __init__(self, model_name="qwen3:8b", max_retries=2):
        self.model_name = model_name
        self.max_retries = max_retries
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # required by OpenAI client, but ignored by Ollama
        )

    def extract_graph(self, text: str) -> Tuple[RawGraphExtraction, str, list[str]]:
        """Returns (RawGraphExtraction, status, warnings)"""
        warnings = []

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Extract entities and relationships from this text:\n\n{text}"},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )

                content = response.choices[0].message.content
                if content:
                    # Strip any <think>...</think> blocks Qwen3 might still include
                    if "<think>" in content:
                        content = content[content.rfind("</think>") + len("</think>"):].strip()
                    data = json.loads(content)
                    return RawGraphExtraction(**data), "SUCCESS", warnings
                else:
                    warnings.append(f"Attempt {attempt + 1}: Empty response from Ollama.")

            except Exception as e:
                warnings.append(f"Attempt {attempt + 1}: Error during Ollama extraction: {e}")

            time.sleep(1)

        return RawGraphExtraction(), "FAILED", warnings
