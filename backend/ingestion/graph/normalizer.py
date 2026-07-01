import re
from typing import Dict
from models.graph import RawGraphExtraction, ExtractionMetadata, GraphDocument, Entity, Relationship

class GraphNormalizer:
    @staticmethod
    def _generate_canonical_id(name: str) -> str:
        """Generates a stable, slugified ID from a name."""
        if not name:
            return "unknown"
        # Lowercase, replace non-alphanumeric with underscores, strip leading/trailing underscores
        slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        return slug or "unknown"

    @staticmethod
    def normalize(chunk_id: str, document_id: str, raw_graph: RawGraphExtraction, metadata: ExtractionMetadata) -> GraphDocument:
        """Stateless normalization: generates IDs and maps relationships."""
        normalized_entities: Dict[str, Entity] = {}
        normalized_relationships = []

        # 1. Normalize Entities and generate IDs
        for raw_ent in raw_graph.entities:
            canonical_id = GraphNormalizer._generate_canonical_id(raw_ent.name)
            
            # Simple deduplication within the same chunk
            if canonical_id not in normalized_entities:
                normalized_entities[canonical_id] = Entity(
                    id=canonical_id,
                    name=raw_ent.name,
                    type=raw_ent.type,
                    properties={}
                )
            else:
                # If we encounter the exact same ID, we just keep the first one 
                # (future resolvers could merge properties)
                pass

        # 2. Normalize Relationships to point to canonical IDs
        for raw_rel in raw_graph.relationships:
            source_id = GraphNormalizer._generate_canonical_id(raw_rel.source_entity_name)
            target_id = GraphNormalizer._generate_canonical_id(raw_rel.target_entity_name)
            
            # Only add relationship if both source and target were successfully extracted as entities
            if source_id in normalized_entities and target_id in normalized_entities:
                normalized_relationships.append(Relationship(
                    source=source_id,
                    target=target_id,
                    relationship_type=raw_rel.relationship_type,
                    confidence=raw_rel.confidence,
                    evidence=raw_rel.evidence
                ))

        return GraphDocument(
            chunk_id=chunk_id,
            document_id=document_id,
            entities=list(normalized_entities.values()),
            relationships=normalized_relationships,
            metadata=metadata
        )
