from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs


INDEX_PATH = MEMORY_DIR / "semantic_vector" / "index.json"
TOKEN_RE = re.compile(r"[\wÀ-ÿ]+", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) > 2]


def _vector(text: str) -> dict[str, float]:
    counts = Counter(_tokens(text))
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {key: value / norm for key, value in counts.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def _load() -> list[dict]:
    ensure_project_dirs()
    if not INDEX_PATH.exists():
        return []
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items: list[dict]) -> Path:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    return INDEX_PATH


def add_document(source: str, content: str, metadata: dict | None = None) -> Path:
    items = _load()
    items.append(
        {
            "source": source,
            "content": content,
            "metadata": metadata or {},
            "vector": _vector(content),
            "indexed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    )
    return _save(items)


def rebuild_memory_index() -> Path:
    ensure_project_dirs()
    items: list[dict] = []
    roots = [MEMORY_DIR]
    excluded_parts = {"semantic_vector", "__pycache__"}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in excluded_parts for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml"}:
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                if content.strip():
                    items.append(
                        {
                            "source": str(path.relative_to(MEMORY_DIR)),
                            "content": content[:20000],
                            "metadata": {"path": str(path)},
                            "vector": _vector(content),
                            "indexed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        }
                    )
    return _save(items)


def search(query: str, limit: int = 5) -> list[dict]:
    qv = _vector(query)
    scored = []
    for item in _load():
        score = _cosine(qv, item.get("vector", {}))
        if score > 0:
            scored.append(
                {
                    "score": round(score, 4),
                    "source": item.get("source"),
                    "metadata": item.get("metadata", {}),
                    "excerpt": item.get("content", "")[:1000],
                }
            )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
