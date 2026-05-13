from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs


REGISTRY_PATH = MEMORY_DIR / "memory_lifecycle_registry.json"
LAYERS = {"short_term", "medium_term", "long_term", "archive_only"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load() -> dict[str, dict]:
    ensure_project_dirs()
    if not REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(rows: dict[str, dict]) -> Path:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return REGISTRY_PATH


def register_memory(text: str, *, layer: str = "short_term", source: str = "unknown", confidence: float = 0.5, expiry_days: int | None = None) -> dict:
    if layer not in LAYERS:
        raise ValueError(f"invalid memory layer: {layer}")
    rows = _load()
    memory_id = f"mem-{len(rows)+1:06d}"
    expiry = None
    if expiry_days is not None:
        expiry = (datetime.now(timezone.utc) + timedelta(days=expiry_days)).isoformat().replace("+00:00", "Z")
    row = {
        "id": memory_id,
        "text": text,
        "layer": layer,
        "confidence": confidence,
        "source": source,
        "created_at": _now(),
        "last_seen": _now(),
        "expiry": expiry,
        "promotion_score": 0,
        "contradicts": [],
        "status": "active",
    }
    rows[memory_id] = row
    _save(rows)
    return row


def update_memory(memory_id: str, **updates) -> dict:
    rows = _load()
    if memory_id not in rows:
        raise KeyError(memory_id)
    rows[memory_id].update(updates)
    rows[memory_id]["last_seen"] = _now()
    _save(rows)
    return rows[memory_id]


def promote_memory(memory_id: str) -> dict:
    row = _load()[memory_id]
    next_layer = {"short_term": "medium_term", "medium_term": "long_term"}.get(row["layer"], row["layer"])
    return update_memory(memory_id, layer=next_layer, promotion_score=row.get("promotion_score", 0) + 1)


def demote_memory(memory_id: str) -> dict:
    row = _load()[memory_id]
    next_layer = {"long_term": "medium_term", "medium_term": "short_term"}.get(row["layer"], row["layer"])
    return update_memory(memory_id, layer=next_layer)


def expire_memory(memory_id: str) -> dict:
    return update_memory(memory_id, status="archived", layer="archive_only")


def mark_conflict(memory_a: str, memory_b: str) -> dict:
    rows = _load()
    for left, right in ((memory_a, memory_b), (memory_b, memory_a)):
        row = rows[left]
        row.setdefault("contradicts", [])
        if right not in row["contradicts"]:
            row["contradicts"].append(right)
        row["status"] = "conflicted"
    _save(rows)
    return {"conflicted": [memory_a, memory_b]}


def review_memory(memory_id: str) -> dict:
    row = _load()[memory_id]
    expired = False
    if row.get("expiry"):
        expired = datetime.fromisoformat(row["expiry"].replace("Z", "+00:00")) <= datetime.now(timezone.utc)
    if expired:
        row = expire_memory(memory_id)
    elif row.get("promotion_score", 0) >= 2 and row["layer"] != "long_term":
        row = promote_memory(memory_id)
    return row
