import logging
from models.graph import GraphDocument

class EntityResolver:
    """
    A dedicated pipeline stage for entity resolution.
    Currently a no-op, serving as an extension point for future deduplication,
    alias resolution (e.g., 'Picasso' -> 'Pablo Picasso'), and graph merging.
    """
    def resolve(self, graph_document: GraphDocument) -> GraphDocument:
        # For now, simply return the graph document unchanged.
        # Logging to verify it's part of the pipeline.
        logging.debug(f"EntityResolver processed GraphDocument for chunk {graph_document.chunk_id} (No-op)")
        return graph_document
