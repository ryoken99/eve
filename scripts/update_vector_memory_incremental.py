from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from local_embedding_provider import EMBEDDING_MODEL, embed_text


EVE_ROOT = Path(__file__).resolve().parents[1]
CHROMA_PATH = EVE_ROOT / "memory" / "vector" / "chroma"
VECTOR_MANIFEST_PATH = EVE_ROOT / "memory" / "vector" / "manifests" / "vector_memory_manifest.json"
IDENTITY_CHUNKS_PATH = EVE_ROOT / "memory" / "_processed" / "chunks" / "identity_card_chunks.jsonl"


COLLECTIONS = {
    "all": "eve_all_memory",
    "private": "eve_private_memory",
    "identity": "eve_identity_memory",
    "entities": "eve_entities_memory",
    "agents": "eve_agents_memory",
    "language": "eve_language_memory",
    "projects": "eve_projects_memory",
    "lore": "eve_lore_memory",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def get_client():
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH), settings=Settings(anonymized_telemetry=False))


def get_collection(client, name: str):
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def metadata_for_chroma(chunk: dict) -> dict[str, str | int | float | bool]:
    allowed: dict[str, str | int | float | bool] = {}
    for key, value in chunk.items():
        if key == "content":
            continue
        if value is None:
            value = ""
        if isinstance(value, (str, int, float, bool)):
            allowed[key] = value
        else:
            allowed[key] = json.dumps(value, ensure_ascii=False)
    return allowed


def target_collections(chunk: dict) -> set[str]:
    targets = {COLLECTIONS["all"]}
    sensitivity = str(chunk.get("sensitivity", "")).lower()
    category = str(chunk.get("category", "")).lower()
    entity_category = str(chunk.get("entity_category", "")).lower()
    source_type = str(chunk.get("source_type", "")).lower()
    if "private" in sensitivity:
        targets.add(COLLECTIONS["private"])
    if source_type == "identity_card" or category == "identity_card":
        targets.add(COLLECTIONS["identity"])
    if entity_category in {"entities", "sandro_core", "bubu_private", "eve_identity", "pc_runtime"} or category in {"entities", "sandro_core", "bubu_private", "eve_identity", "pc_runtime"}:
        targets.add(COLLECTIONS["entities"])
    if entity_category == "agents" or category == "agents":
        targets.add(COLLECTIONS["agents"])
    if entity_category == "language" or category == "language":
        targets.add(COLLECTIONS["language"])
    if entity_category == "projects" or category in {"projects", "project"}:
        targets.add(COLLECTIONS["projects"])
    if entity_category == "lore_simulation" or category in {"lore", "lore_simulation"} or sensitivity == "lore":
        targets.add(COLLECTIONS["lore"])
    return targets


def folder_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def load_manifest() -> dict[str, Any]:
    if not VECTOR_MANIFEST_PATH.exists():
        return {}
    return json.loads(VECTOR_MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(data: dict[str, Any]) -> None:
    VECTOR_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    VECTOR_MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def update(input_path: Path = IDENTITY_CHUNKS_PATH) -> dict[str, Any]:
    chunks = [chunk for chunk in load_jsonl(input_path) if str(chunk.get("content", "")).strip()]
    client = get_client()
    stats: Counter = Counter()
    failures = []
    dimensions = None
    for chunk in chunks:
        try:
            embedding = embed_text(chunk["content"])
            dimensions = dimensions or len(embedding)
            metadata = metadata_for_chroma(chunk)
            for collection_name in target_collections(chunk):
                col = get_collection(client, collection_name)
                col.upsert(
                    ids=[chunk["chunk_id"]],
                    documents=[chunk["content"]],
                    embeddings=[embedding],
                    metadatas=[metadata],
                )
                stats[collection_name] += 1
        except Exception as exc:
            failures.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "source_file": chunk.get("source_file"),
                    "error": type(exc).__name__,
                }
            )

    collection_counts = {}
    for item in client.list_collections():
        name = item if isinstance(item, str) else item.name
        collection_counts[name] = client.get_collection(name).count()

    manifest = load_manifest()
    manifest["last_incremental_update_at"] = utc_now()
    manifest["last_incremental_update"] = {
        "source": str(input_path),
        "embedding_backend": "ollama_local_http",
        "embedding_model": EMBEDDING_MODEL,
        "chunks_seen": len(chunks),
        "chunks_indexed": len(chunks) - len(failures),
        "chunks_failed": len(failures),
        "embedding_dimensions": dimensions,
        "collections_touched": dict(stats),
        "failures": failures[:50],
    }
    manifest["collections"] = collection_counts
    manifest["folder_size_bytes"] = folder_size(CHROMA_PATH)
    save_manifest(manifest)

    return {
        "ok": len(failures) == 0,
        "input": str(input_path),
        "chunks_seen": len(chunks),
        "chunks_indexed": len(chunks) - len(failures),
        "chunks_failed": len(failures),
        "collections_touched": dict(stats),
        "collection_counts": collection_counts,
        "manifest": str(VECTOR_MANIFEST_PATH),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Incrementally upsert local Eve memory chunks into Chroma.")
    parser.add_argument("--input", type=Path, default=IDENTITY_CHUNKS_PATH)
    args = parser.parse_args()
    print(json.dumps(update(args.input), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
