from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs
from memory.semantic_vector.chunker import chunk_text


EMBEDDING_INDEX_PATH = MEMORY_DIR / "semantic_vector" / "embedding_index.json"
DEFAULT_NEURAL_MODEL = os.environ.get("EVE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_MODEL = None


def _hash_embedding(text: str, dims: int = 64) -> list[float]:
    buckets = [0.0] * dims
    for token in re.findall(r"[\wÀ-ÿ]+", text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dims
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        buckets[index] += sign
    norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
    return [round(value / norm, 6) for value in buckets]


def embedding_backend() -> str:
    if os.environ.get("EVE_DISABLE_NEURAL_EMBEDDINGS") == "1":
        return "local-hash-embedding"
    try:
        import sentence_transformers  # type: ignore  # noqa: F401
        return f"sentence-transformers:{DEFAULT_NEURAL_MODEL}"
    except Exception:
        return "local-hash-embedding"


def embed_text(text: str) -> list[float]:
    global _MODEL
    if embedding_backend().startswith("sentence-transformers"):
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            if _MODEL is None:
                _MODEL = SentenceTransformer(DEFAULT_NEURAL_MODEL)
            vector = _MODEL.encode([text], normalize_embeddings=True)[0]
            return [round(float(value), 6) for value in vector.tolist()]
        except Exception:
            return _hash_embedding(text)
    return _hash_embedding(text)


def add_embedded_document(source: str, content: str, metadata: dict | None = None) -> Path:
    ensure_project_dirs()
    rows = []
    if EMBEDDING_INDEX_PATH.exists():
        try:
            rows = json.loads(EMBEDDING_INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            rows = []
    for index, chunk in enumerate(chunk_text(content)):
        rows.append(
            {
                "chunk_id": f"{source}:{index}",
                "source": source,
                "content": chunk,
                "embedding": embed_text(chunk),
                "metadata": metadata or {},
                "indexed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "backend": embedding_backend(),
            }
        )
    EMBEDDING_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    EMBEDDING_INDEX_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return EMBEDDING_INDEX_PATH


def load_embedding_index() -> list[dict]:
    if not EMBEDDING_INDEX_PATH.exists():
        return []
    return json.loads(EMBEDDING_INDEX_PATH.read_text(encoding="utf-8"))
