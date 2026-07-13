import json
import dataclasses
from models.chunk import Chunk, RetrievedChunk

# Fields accepted by each constructor — used to filter out extra dataclass fields
_CHUNK_FIELDS = {f.name for f in dataclasses.fields(Chunk)}
_RC_FIELDS = {f.name for f in dataclasses.fields(RetrievedChunk)}


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, RetrievedChunk):
            return {
                "__type__": "RetrievedChunk",
                # Use dataclasses.asdict for safe, field-only serialization
                "chunk": dataclasses.asdict(obj.chunk),
                "vector_score": obj.vector_score,
                "bm25_score": obj.bm25_score,
                "rerank_score": obj.rerank_score,
                "rrf_score": obj.rrf_score,
            }
        elif isinstance(obj, Chunk):
            return {"__type__": "Chunk", **dataclasses.asdict(obj)}
        return super().default(obj)


def object_hook(dct):
    t = dct.get("__type__")
    if t == "RetrievedChunk":
        # chunk value is a plain dict at this point (no __type__ key)
        chunk_data = dct.get("chunk", {})
        # Filter to only known Chunk fields to avoid unexpected-keyword-argument TypeError
        safe_chunk = {k: v for k, v in chunk_data.items() if k in _CHUNK_FIELDS}
        chunk = Chunk(**safe_chunk)
        safe_rc = {k: dct[k] for k in ("vector_score", "bm25_score", "rerank_score", "rrf_score") if k in dct}
        return RetrievedChunk(chunk=chunk, **safe_rc)
    elif t == "Chunk":
        data = {k: v for k, v in dct.items() if k in _CHUNK_FIELDS}
        return Chunk(**data)
    return dct


class CacheSerializer:
    @staticmethod
    def serialize(obj):
        return json.dumps(obj, cls=ObjectEncoder)

    @staticmethod
    def deserialize(data: str):
        if not data:
            return None
        try:
            return json.loads(data, object_hook=object_hook)
        except Exception:
            return None

