from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings

from local_embedding_provider import check_ollama_embedding_model


EVE_ROOT = Path(__file__).resolve().parents[1]
CHROMA_PATH = EVE_ROOT / "memory" / "vector" / "chroma"
MANIFEST_PATH = EVE_ROOT / "memory" / "vector" / "manifests" / "vector_memory_manifest.json"


def folder_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def collection_name(item) -> str:
    return item if isinstance(item, str) else item.name


def main() -> int:
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    collections = {}
    chroma_exists = CHROMA_PATH.exists()
    if chroma_exists:
        client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False),
        )
        for item in client.list_collections():
            name = collection_name(item)
            try:
                collections[name] = client.get_collection(name).count()
            except Exception as exc:
                collections[name] = f"error:{type(exc).__name__}"

    payload = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "chroma_exists": chroma_exists,
        "chroma_path": str(CHROMA_PATH),
        "folder_size_bytes": folder_size(CHROMA_PATH),
        "manifest_exists": MANIFEST_PATH.exists(),
        "manifest_path": str(MANIFEST_PATH),
        "collections": collections,
        "model_used": manifest.get("embedding_model"),
        "backend": manifest.get("embedding_backend"),
        "last_build": manifest.get("built_at"),
        "total_chunks_indexed": manifest.get("chunks_indexed"),
        "chunks_failed": manifest.get("chunks_failed"),
        "embedding_dimensions": manifest.get("embedding_dimensions"),
        "ollama_status": check_ollama_embedding_model(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
