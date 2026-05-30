from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.config import Settings

from local_embedding_provider import EMBEDDING_MODEL, check_ollama_embedding_model, embed_text


EVE_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = EVE_ROOT / "memory" / "_processed" / "chunks" / "imported_memory_chunks.jsonl"
CHROMA_PATH = EVE_ROOT / "memory" / "vector" / "chroma"
MANIFEST_PATH = EVE_ROOT / "memory" / "vector" / "manifests" / "vector_memory_manifest.json"

COLLECTIONS = {
    "all": "eve_all_memory",
    "private": "eve_private_memory",
    "lore": "eve_lore_memory",
    "projects": "eve_projects_memory",
    "agents": "eve_agents_memory",
    "language": "eve_language_memory",
}

SPECIFIC_CATEGORY_MAP = {
    "lore_simulation": "lore",
    "projects": "projects",
    "agents": "agents",
    "language": "language",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_chunks(path: Path = CHUNKS_PATH) -> list[dict]:
    chunks: list[dict] = []
    if not path.exists():
        return chunks
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            chunks.append(json.loads(line))
    return chunks


def sanitize_metadata(chunk: dict) -> dict:
    keys = [
        "chunk_id",
        "source_file",
        "source_path",
        "source_name",
        "version",
        "category",
        "sensitivity",
        "importance_hint",
        "chunk_index",
        "content_hash",
        "imported_at",
    ]
    metadata = {}
    for key in keys:
        value = chunk.get(key, "")
        if value is None:
            value = ""
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
        else:
            metadata[key] = json.dumps(value, ensure_ascii=False)
    return metadata


def target_collection_keys(chunk: dict) -> set[str]:
    keys = {"all"}
    sensitivity = str(chunk.get("sensitivity", "")).lower()
    category = str(chunk.get("category", "")).lower()
    if "private" in sensitivity:
        keys.add("private")
    mapped = SPECIFIC_CATEGORY_MAP.get(category)
    if mapped:
        keys.add(mapped)
    return keys


def collection(client: chromadb.PersistentClient, name: str):
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def add_to_collections(client, chunk: dict, embedding: list[float], stats: Counter) -> None:
    metadata = sanitize_metadata(chunk)
    document = chunk.get("content", "")
    chunk_id = str(chunk.get("chunk_id"))
    for key in target_collection_keys(chunk):
        name = COLLECTIONS[key]
        col = collection(client, name)
        col.upsert(
            ids=[chunk_id],
            documents=[document],
            metadatas=[metadata],
            embeddings=[embedding],
        )
        stats[name] += 1


def folder_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def build(limit: int | None = None) -> dict:
    model_check = check_ollama_embedding_model()
    if not model_check.get("ok"):
        raise RuntimeError(model_check.get("error") or "Ollama embedding model is not available.")

    chunks = [chunk for chunk in load_chunks() if str(chunk.get("content", "")).strip()]
    if limit is not None:
        chunks = chunks[:limit]

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    started = time.perf_counter()
    stats: Counter = Counter()
    failures: list[dict] = []
    embedding_dim = None
    categories: Counter = Counter()
    sensitivities: Counter = Counter()

    for index, chunk in enumerate(chunks, start=1):
        content = str(chunk.get("content", "")).strip()
        try:
            embedding = embed_text(content)
            embedding_dim = embedding_dim or len(embedding)
            add_to_collections(client, chunk, embedding, stats)
            categories[str(chunk.get("category", "unknown"))] += 1
            sensitivities[str(chunk.get("sensitivity", "unknown"))] += 1
        except Exception as exc:
            failures.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "source_file": chunk.get("source_file"),
                    "error": type(exc).__name__,
                }
            )
        if index % 25 == 0:
            print(json.dumps({"progress": index, "total": len(chunks), "failures": len(failures)}, ensure_ascii=False))

    duration = round(time.perf_counter() - started, 3)
    collection_counts = {}
    for name in COLLECTIONS.values():
        try:
            collection_counts[name] = collection(client, name).count()
        except Exception:
            collection_counts[name] = None

    manifest = {
        "built_at": utc_now(),
        "embedding_backend": "ollama_local_http",
        "embedding_model": EMBEDDING_MODEL,
        "ollama_base_url": "http://localhost:11434",
        "chunks_input": str(CHUNKS_PATH),
        "chroma_path": str(CHROMA_PATH),
        "chunks_seen": len(chunks),
        "chunks_indexed": len(chunks) - len(failures),
        "chunks_failed": len(failures),
        "embedding_dimensions": embedding_dim,
        "collections": collection_counts,
        "upsert_operations_by_collection": dict(stats),
        "categories": dict(categories),
        "sensitivities": dict(sensitivities),
        "failures": failures[:50],
        "duration_seconds": duration,
        "folder_size_bytes": folder_size(CHROMA_PATH),
        "privacy": "All embeddings were produced locally through Ollama. No private memory was sent to an external embedding API.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Eve local vector memory from imported chunks.")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for diagnostics.")
    args = parser.parse_args()
    manifest = build(limit=args.limit)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
