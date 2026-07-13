import time
import logging
from collections import OrderedDict
from models.chunk import RetrievedChunk
from generation.prompt_builder import PromptBuilder
from generation.llm import generate_answer

class GenerationService:
    def __init__(self, max_context_tokens: int):
        self.max_context_tokens = max_context_tokens

    def _select_diverse_chunks(self, reranked_results: list[RetrievedChunk]):
        """
        Diversity-aware chunk selection.
        Round 1: Pick the highest-scored chunk from each unique section (chapter)
                 to guarantee breadth across all topics.
        Round 2: Fill remaining token budget with next-best chunks by score
                 for additional depth.
        """
        if not reranked_results:
            return []

        # Group chunks by section (chapter). Use OrderedDict to preserve
        # insertion order (highest-scored first since reranked_results is sorted).
        groups: dict[str, list[RetrievedChunk]] = OrderedDict()
        for rc in reranked_results:
            key = rc.chunk.section or f"page_{rc.chunk.page}"
            if key not in groups:
                groups[key] = []
            groups[key].append(rc)

        selected = []
        used_ids = set()
        total_tokens = 0

        # Round 1: One chunk per section for breadth
        for section_key, group in groups.items():
            best = group[0]  # Already sorted by rerank score
            if best.chunk.chunk_id in used_ids:
                continue
            if total_tokens + best.chunk.token_count <= self.max_context_tokens:
                selected.append(best.chunk)
                used_ids.add(best.chunk.chunk_id)
                total_tokens += best.chunk.token_count

        # Round 2: Fill remaining budget with depth (best remaining chunks by score)
        for rc in reranked_results:
            if rc.chunk.chunk_id in used_ids:
                continue
            if total_tokens + rc.chunk.token_count <= self.max_context_tokens:
                selected.append(rc.chunk)
                used_ids.add(rc.chunk.chunk_id)
                total_tokens += rc.chunk.token_count

        logging.info(
            f"Diversity selector: {len(groups)} sections found, "
            f"{len(selected)} chunks selected, {total_tokens} tokens used "
            f"(budget: {self.max_context_tokens})"
        )
        return selected

    def generate(self, query: str, reranked_results: list[RetrievedChunk], memory_context=None) -> str:
        top_chunks = self._select_diverse_chunks(reranked_results)

        prompt = PromptBuilder().build(query, top_chunks, memory_context)
        logging.info("Generating answer...\n")
        
        llm_start = time.time()
        llm_time = time.time() - llm_start

        logging.info("=" * 80)
        logging.info("Generation Timing Metrics")
        logging.info("=" * 80)

        return generate_answer(prompt)

