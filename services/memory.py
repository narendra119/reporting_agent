import hashlib
import os
import uuid

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION    = "reporting_memory"
VECTOR_SIZE   = 768                                     # nomic-embed-text output size
QDRANT_URL    = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL   = "nomic-embed-text"

# Ollama exposes an OpenAI-compatible /v1 API — no extra dependency needed
_ollama = OpenAI(base_url=f"{OLLAMA_URL}/v1", api_key="ollama")
_qdrant = QdrantClient(url=QDRANT_URL)


def _ensure_collection() -> None:
    existing = {c.name for c in _qdrant.get_collections().collections}
    if COLLECTION not in existing:
        _qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def _embed(text: str) -> list[float]:
    res = _ollama.embeddings.create(model=EMBED_MODEL, input=text)
    return res.data[0].embedding


def _fact_id(fact: str) -> str:
    """Stable UUID derived from the fact text — re-saving the same fact upserts, not duplicates."""
    return str(uuid.UUID(hashlib.md5(fact.strip().lower().encode()).hexdigest()))


def save(facts: list[str]) -> int:
    """Embed and upsert each fact. Returns the number of facts stored."""
    _ensure_collection()
    points = [
        PointStruct(id=_fact_id(f), vector=_embed(f), payload={"text": f})
        for f in facts
        if f.strip()
    ]
    if points:
        _qdrant.upsert(collection_name=COLLECTION, points=points)
    return len(points)


def search(query: str, top_k: int = 5) -> list[str]:
    """Return the top-k most relevant facts for the given query."""
    _ensure_collection()
    result = _qdrant.query_points(
        collection_name=COLLECTION,
        query=_embed(query),
        limit=top_k,
    )
    return [h.payload["text"] for h in result.points]
