from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs


def extract_lesson(source: str, problem: str, fix: str, lesson: str) -> Path:
    ensure_project_dirs()
    path = MEMORY_DIR / "procedural" / "lessons.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {timestamp} - {source}\n")
        handle.write(f"- Problema: {problem.strip()}\n")
        handle.write(f"- Correcao: {fix.strip()}\n")
        handle.write(f"- Licao: {lesson.strip()}\n")
    return path
