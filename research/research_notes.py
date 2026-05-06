from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs


def append_world_learning(text: str) -> Path:
    return _append("world", "world_learning.md", text)


def append_technology_learning(text: str) -> Path:
    return _append("technology", "technology_learning.md", text)


def append_research_candidate(text: str) -> Path:
    return _append("technology", "research_candidates.md", text)


def _append(layer: str, name: str, text: str) -> Path:
    ensure_project_dirs()
    path = MEMORY_DIR / layer / name
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"- {stamp}: {text}\n")
    return path
