import time
import logging
from typing import Tuple
from ingestion.graph.ollama_client import OllamaGraphClient
from models.graph import RawGraphExtraction, ExtractionMetadata

class GraphExtractor:
    def __init__(self):
        self.client = OllamaGraphClient()

    def extract(self, text: str) -> Tuple[RawGraphExtraction, ExtractionMetadata]:
        start_time = time.time()
        
        raw_result, status, warnings = self.client.extract_graph(text)
        
        processing_time_ms = (time.time() - start_time) * 1000.0
        
        metadata = ExtractionMetadata(
            processing_time_ms=processing_time_ms,
            model_name=self.client.model_name,
            status=status,
            warnings=warnings
        )
        
        if status == "SUCCESS":
            logging.info(f"Extracted {len(raw_result.entities)} entities and {len(raw_result.relationships)} relationships in {processing_time_ms:.1f}ms")
        else:
            logging.warning(f"Graph extraction failed in {processing_time_ms:.1f}ms. Warnings: {warnings}")
            
        return raw_result, metadata
