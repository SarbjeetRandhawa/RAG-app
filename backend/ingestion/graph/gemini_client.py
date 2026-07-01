import os
from google import genai
from google.genai import types
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

Output format: JSON matching the RawGraphExtraction schema.
"""

class GeminiGraphClient:
    def __init__(self, model_name="gemini-2.5-flash", max_retries=3):
        self.model_name = model_name
        self.max_retries = max_retries
        self.client = None
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if gemini_api_key:
            try:
                self.client = genai.Client(api_key=gemini_api_key)
            except Exception as e:
                logging.error(f"Failed to initialize Gemini Client: {e}")

    def extract_graph(self, text: str) -> Tuple[RawGraphExtraction, str, list[str]]:
        """
        Returns (RawGraphExtraction, status, warnings)
        """
        if not self.client:
            return RawGraphExtraction(), "FAILED", ["Gemini client not initialized"]

        warnings = []
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RawGraphExtraction,
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.1,
                    )
                )
                if response.text:
                    data = json.loads(response.text)
                    return RawGraphExtraction(**data), "SUCCESS", warnings
                else:
                    warnings.append(f"Attempt {attempt + 1}: Empty response from Gemini.")
            except Exception as e:
                warnings.append(f"Attempt {attempt + 1}: Error during Gemini extraction: {e}")
            
            time.sleep(2 ** attempt)  # Exponential backoff

        return RawGraphExtraction(), "FAILED", warnings
