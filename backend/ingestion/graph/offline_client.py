import json
import logging
import time
from typing import Tuple

from llama_cpp import Llama
from models.graph import RawGraphExtraction

MODEL_PATH = r"D:\Rag Learning\backend\models\Qwen3-8B-Q4_K_M.gguf"

SYSTEM_PROMPT = """You are an expert NLP graph extraction system. /no_think
Extract entities and relationships from the provided text.

Entity Types (pick one): PERSON, ORGANIZATION, LOCATION, CONCEPT, EVENT, PRODUCT

Preferred Relationship Ontology (use these if possible): 
CREATED, WORKS_FOR, LOCATED_IN, PART_OF, MEMBER_OF, USES, DEPENDS_ON, REFERENCES, OWNS, RELATED_TO

Rules:
1. Only extract information explicitly present in the text.
2. For entities: provide 'name' exactly as it appears, and 'type'.
3. For relationships: provide 'source_entity_name' and 'target_entity_name' matching the entity names exactly.
4. Provide 'relationship_type', 'confidence' (0.0-1.0), and 'evidence' (exact substring from text).
5. Do not hallucinate. If unsure, set confidence < 0.5.

You MUST return valid JSON in this exact format:
{
  "entities": [{"name": "...", "type": "..."}],
  "relationships": [{"source_entity_name": "...", "target_entity_name": "...", "relationship_type": "...", "confidence": 0.9, "evidence": "..."}]
}"""

_llm_instance = None

def get_llm() -> Llama:
    """Lazy-load the model once and reuse it (singleton pattern)."""
    global _llm_instance
    if _llm_instance is None:
        logging.info(f"Loading offline model from {MODEL_PATH}...")
        _llm_instance = Llama(
            model_path=MODEL_PATH,
            n_ctx=4096,        # Context window
            n_threads=8,       # CPU threads
            n_gpu_layers=0,    # CPU only
            verbose=False,
        )
        logging.info("Offline model loaded successfully.")
    return _llm_instance

class OfflineGraphClient:
    def __init__(self, max_retries=2):
        self.model_name = "Qwen3-8B-Q4_K_M (offline)"
        self.max_retries = max_retries

    def extract_graph(self, text: str) -> Tuple[RawGraphExtraction, str, list[str]]:
        """Returns (RawGraphExtraction, status, warnings)"""
        warnings = []
        
        # Truncate very long chunks to avoid exceeding context window
        max_chars = 1500
        if len(text) > max_chars:
            text = text[:max_chars]
            warnings.append(f"Chunk truncated to {max_chars} chars to fit context window.")

        for attempt in range(self.max_retries):
            try:
                llm = get_llm()
                response = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Extract entities and relationships from the following text:\n\n{text}"},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=1024,
                )
                
                content = response["choices"][0]["message"]["content"]
                if content:
                    data = json.loads(content)
                    return RawGraphExtraction(**data), "SUCCESS", warnings
                else:
                    warnings.append(f"Attempt {attempt + 1}: Empty response from model.")
            except Exception as e:
                warnings.append(f"Attempt {attempt + 1}: Error during offline extraction: {e}")
            
            time.sleep(1)

        return RawGraphExtraction(), "FAILED", warnings
