import os
from openai import OpenAI
import json
import logging
import time
from dotenv import load_dotenv
from typing import Tuple

from models.graph import RawGraphExtraction

load_dotenv()

SYSTEM_PROMPT = """
You are an expert NLP graph extraction system.
Extract entities and relationships from the provided text according to the following strict schema.

Entity Types: PERSON, ORGANIZATION, LOCATION, CONCEPT, EVENT, PRODUCT

Relationships:
- Extract relationships between the entities you found.
- Preferred Relationship Ontology: CREATED, WORKS_FOR, LOCATED_IN, PART_OF, MEMBER_OF, USES, DEPENDS_ON, REFERENCES, OWNS, RELATED_TO.
- If a relationship doesn't fit the preferred ontology, you may use a short, descriptive UPPERCASE string.

Rules:
1. Only extract information present in the text.
2. For entities, provide the 'name' exactly as it appears in text, and the 'type'.
3. For relationships, provide the 'source_entity_name' and 'target_entity_name' matching exactly the extracted entity names.
4. Provide the 'relationship_type' as a string.
5. Provide a 'confidence' score (0.0 to 1.0) and 'evidence' (the exact substring from the text supporting this relationship).
6. Do not hallucinate relationships.

Output format: Return valid JSON matching the RawGraphExtraction schema exactly.
"""

class GroqGraphClient:
    def __init__(self, model_name="llama-3.3-70b-versatile", max_retries=3):
        self.model_name = model_name
        self.max_retries = max_retries
        self.client = None
        
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if groq_api_key:
            try:
                self.client = OpenAI(
                    api_key=groq_api_key,
                    base_url="https://api.groq.com/openai/v1",
                )
            except Exception as e:
                logging.error(f"Failed to initialize Groq Client: {e}")

    def extract_graph(self, text: str) -> Tuple[RawGraphExtraction, str, list[str]]:
        """
        Returns (RawGraphExtraction, status, warnings)
        """
        if not self.client:
            return RawGraphExtraction(), "FAILED", ["Groq client not initialized"]

        warnings = []
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                
                content = response.choices[0].message.content
                if content:
                    data = json.loads(content)
                    return RawGraphExtraction(**data), "SUCCESS", warnings
                else:
                    warnings.append(f"Attempt {attempt + 1}: Empty response from Groq.")
            except Exception as e:
                warnings.append(f"Attempt {attempt + 1}: Error during Groq extraction: {e}")
            
            time.sleep(2 ** attempt)  # Exponential backoff

        return RawGraphExtraction(), "FAILED", warnings
