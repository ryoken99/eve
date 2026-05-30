from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path


EVE_ROOT = Path(__file__).resolve().parents[1]
MEMORY_ROOT = EVE_ROOT / "memory"
MANIFEST_PATH = MEMORY_ROOT / "_system" / "imported_memory_manifest.json"
CHUNKS_PATH = MEMORY_ROOT / "_processed" / "chunks" / "imported_memory_chunks.jsonl"

CANONICAL_DIRS = [
    "_system",
    "_reports",
    "_inbox/imports/memory_v1_to_v7",
    "_processed/chunks",
    "_processed/summaries",
    "_processed/metadata",
    "_processed/classifications",
    "transcripts/raw/webui",
    "transcripts/raw/telegram",
    "transcripts/raw/terminal",
    "transcripts/raw/system",
    "transcripts/tools",
    "transcripts/errors",
    "transcripts/daily_rollups",
    "short_term",
    "medium_term",
    "long_term/sandro",
    "long_term/bubu_private",
    "long_term/eve_identity",
    "long_term/projects",
    "long_term/entities",
    "long_term/agents",
    "long_term/language",
    "long_term/worldbuilding",
    "long_term/health_private",
    "knowledge/world",
    "knowledge/technology",
    "knowledge/science",
    "knowledge/markets",
    "knowledge/culture",
    "personality/taste",
    "personality/style",
    "personality/preferences",
    "dreams/daily",
    "dreams/weekly",
    "dreams/insights",
    "vector/chroma",
    "vector/manifests",
    "runtime/active_context",
    "runtime/pending_tasks",
    "runtime/session_state",
]

LEGACY_DIRS = [
    "archive_only",
    "diary",
    "dream_reports",
    "errors",
    "long_term",
    "medium_term",
    "personality",
    "procedural",
    "semantic_vector",
    "short_term",
    "technology",
    "world",
]


def count_chunks() -> tuple[int, Counter, Counter]:
    categories: Counter = Counter()
    sensitivities: Counter = Counter()
    count = 0
    if not CHUNKS_PATH.exists():
        return count, categories, sensitivities
    for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        count += 1
        chunk = json.loads(line)
        categories[chunk.get("category", "unknown")] += 1
        sensitivities[chunk.get("sensitivity", "unknown")] += 1
    return count, categories, sensitivities


def manifest_count() -> int:
    if not MANIFEST_PATH.exists():
        return 0
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return len(data) if isinstance(data, list) else 0


def memory_files() -> list[Path]:
    if not MEMORY_ROOT.exists():
        return []
    return [path for path in MEMORY_ROOT.rglob("*") if path.is_file()]


def main() -> int:
    files = memory_files()
    today = datetime.now().strftime("%Y-%m-%d")
    chunk_count, categories, sensitivities = count_chunks()
    source_files = [path for path in (MEMORY_ROOT / "_inbox" / "imports" / "memory_v1_to_v7").rglob("*") if path.is_file()] if (MEMORY_ROOT / "_inbox" / "imports" / "memory_v1_to_v7").exists() else []
    today_transcripts = [
        str(path)
        for root in [
            MEMORY_ROOT / "transcripts",
            EVE_ROOT / "logs" / "transcripts",
        ]
        if root.exists()
        for path in root.rglob("*")
        if path.is_file() and (today in path.name or datetime.now().strftime("%d-%m-%y") in path.name)
    ]
    largest = sorted(files, key=lambda path: path.stat().st_size if path.exists() else 0, reverse=True)[:10]
    modified = sorted(files, key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)[:10]
    payload = {
        "memory_root": str(MEMORY_ROOT),
        "canonical_dirs": {item: (MEMORY_ROOT / item).exists() for item in CANONICAL_DIRS},
        "legacy_dirs": {item: (MEMORY_ROOT / item).exists() for item in LEGACY_DIRS},
        "imported_memory_manifest_exists": MANIFEST_PATH.exists(),
        "manifest_source_count": manifest_count(),
        "detected_import_files": len(source_files),
        "chunks_count": chunk_count,
        "categories": dict(categories),
        "sensitivities": dict(sensitivities),
        "memory_total_size_bytes": sum(path.stat().st_size for path in files if path.exists()),
        "today_transcripts_count": len(today_transcripts),
        "today_rollup_exists": (MEMORY_ROOT / "transcripts" / "daily_rollups" / f"{today}_rollup.md").exists(),
        "vector_db_exists": (MEMORY_ROOT / "vector" / "chroma").exists() and any((MEMORY_ROOT / "vector" / "chroma").iterdir()),
        "legacy_semantic_vector_exists": (MEMORY_ROOT / "semantic_vector").exists(),
        "top_10_largest_files": [{"path": str(path), "size": path.stat().st_size} for path in largest],
        "last_10_modified_files": [{"path": str(path), "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()} for path in modified],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
