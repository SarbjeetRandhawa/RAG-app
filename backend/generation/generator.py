import time
import logging
from models.chunk import RetrievedChunk
from generation.prompt_builder import PromptBuilder
from generation.llm import generate_answer

class GenerationService:
    def __init__(self, max_context_tokens: int):
        self.max_context_tokens = max_context_tokens

    def generate(self, query: str, reranked_results: list[RetrievedChunk]) -> str:
        top_chunks = []
        current_tokens = 0
        for rc in reranked_results:
            if current_tokens + rc.chunk.token_count <= self.max_context_tokens:
                top_chunks.append(rc.chunk)
                current_tokens += rc.chunk.token_count
            else:
                break

        prompt = PromptBuilder().build(query, top_chunks)
        logging.info("Generating answer...\n")
        
        llm_start = time.time()
        llm_time = time.time() - llm_start

        logging.info("=" * 80)
        logging.info("Generation Timing Metrics")
        logging.info("=" * 80)

        return generate_answer(prompt)