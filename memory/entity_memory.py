from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import ENTITIES_MEMORY_DIR, ensure_project_dirs
from security.audit_log import log_event


INDEX_PATH = ENTITIES_MEMORY_DIR / "indexes" / "entities.jsonl"
RELATIONS_PATH = ENTITIES_MEMORY_DIR / "relations" / "relations.jsonl"
INDEXABLE_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".py", ".csv"}


def _safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip().lower()).strip("_")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def entity_path(name: str) -> Path:
    ensure_project_dirs()
    safe = _safe_name(name)
    if not safe:
        raise ValueError("Nome de entidade vazio")
    return ENTITIES_MEMORY_DIR / "entities" / f"{safe}.md"


def remember_entity(name: str, kind: str, note: str, metadata: dict | None = None) -> Path:
    ensure_project_dirs()
    path = entity_path(name)
    created = not path.exists()
    with path.open("a", encoding="utf-8") as handle:
        if created:
            handle.write(f"# {name}\n\n")
            handle.write(f"- Tipo: {kind}\n")
            handle.write(f"- Criado: {_now()}\n\n")
        handle.write(f"## {_now()}\n\n{note.strip()}\n\n")
    entry = {
        "timestamp": _now(),
        "name": name,
        "safe_name": _safe_name(name),
        "kind": kind,
        "note": note,
        "path": str(path),
        "metadata": metadata or {},
    }
    with INDEX_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log_event("entity_remembered", entry)
    return path


def relate_entities(source: str, relation: str, target: str, note: str = "") -> Path:
    ensure_project_dirs()
    entry = {
        "timestamp": _now(),
        "source": source,
        "relation": relation,
        "target": target,
        "note": note,
    }
    with RELATIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log_event("entity_relation_recorded", entry)
    return RELATIONS_PATH


def list_entities() -> list[dict]:
    ensure_project_dirs()
    rows = []
    for path in sorted((ENTITIES_MEMORY_DIR / "entities").glob("*.md")):
        rows.append({"name": path.stem, "path": str(path)})
    return rows


def list_base_memory_files() -> list[dict]:
    ensure_project_dirs()
    rows = []
    for path in sorted(ENTITIES_MEMORY_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in INDEXABLE_SUFFIXES:
            rows.append(
                {
                    "path": str(path),
                    "relative": str(path.relative_to(ENTITIES_MEMORY_DIR)),
                    "size": path.stat().st_size,
                    "updated": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
                }
            )
    return rows


def search_entities(query: str, limit: int = 10) -> list[dict]:
    ensure_project_dirs()
    needle = query.lower()
    results = []
    candidates = list((ENTITIES_MEMORY_DIR / "entities").glob("*.md")) + [
        path for path in ENTITIES_MEMORY_DIR.rglob("*") if path.is_file() and path.suffix.lower() in INDEXABLE_SUFFIXES
    ]
    seen = set()
    for path in sorted(candidates):
        if path in seen:
            continue
        seen.add(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        if needle in path.stem.lower() or needle in text.lower():
            idx = text.lower().find(needle)
            excerpt = text[max(0, idx - 250) : idx + 750] if idx >= 0 else text[:1000]
            results.append({"name": path.stem, "path": str(path), "excerpt": excerpt})
    return results[:limit]
