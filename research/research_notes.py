from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs


def append_world_learning(text: str) -> Path:
    path = _append("world", "world_learning.md", text)
    append_daily_learning("world", text)
    return path


def append_technology_learning(text: str) -> Path:
    path = _append("technology", "technology_learning.md", text)
    append_daily_learning("technology", text)
    return path


def append_personality_learning(text: str) -> Path:
    return append_daily_learning("personality", text)


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


def date_key_dd_mm_yy(moment: datetime | None = None) -> str:
    moment = moment or datetime.now()
    return moment.strftime("%d-%m-%y")


def daily_learning_path(kind: str, moment: datetime | None = None) -> Path:
    ensure_project_dirs()
    clean_kind = kind.strip().lower().replace(" ", "_")
    if clean_kind not in {"world", "technology", "personality"}:
        raise ValueError(f"Tipo de aprendizagem desconhecido: {kind}")
    path = MEMORY_DIR / clean_kind / "daily" / f"{date_key_dd_mm_yy(moment)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def append_daily_learning(kind: str, text: str, *, moment: datetime | None = None) -> Path:
    path = daily_learning_path(kind, moment)
    stamp = (moment or datetime.now()).isoformat(timespec="seconds")
    if not path.exists():
        title = {
            "world": "World And Taste Learning",
            "technology": "Technology Learning",
            "personality": "Eve Preference Evolution",
        }[kind.strip().lower().replace(" ", "_")]
        path.write_text(f"# {title} - {date_key_dd_mm_yy(moment)}\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"- {stamp}: {text.strip()}\n")
    return path
