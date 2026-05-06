from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs
from memory.diary_manager import diary_path, read_diary, today_key


def read_memory_file(layer: str, name: str) -> str:
    path = MEMORY_DIR / layer / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_memory_file(layer: str, name: str, content: str) -> Path:
    ensure_project_dirs()
    path = MEMORY_DIR / layer / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def append_memory_file(layer: str, name: str, content: str) -> Path:
    ensure_project_dirs()
    path = MEMORY_DIR / layer / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(content)
        if not content.endswith("\n"):
            fh.write("\n")
    return path


def context_bundle(max_chars: int = 12000) -> str:
    pieces = []
    for rel in (
        ("long_term", "eve_constitution.md"),
        ("long_term", "eve_mission.md"),
        ("long_term", "sandro_profile.md"),
        ("medium_term", "recent_projects.md"),
        ("short_term", "current_session.md"),
    ):
        text = read_memory_file(*rel).strip()
        if text:
            pieces.append(f"## memory/{rel[0]}/{rel[1]}\n{text}")
    diary = read_diary().strip()
    if diary:
        pieces.append(f"## diary/{today_key()}.md\n{diary[-4000:]}")
    bundle = "\n\n".join(pieces)
    return bundle[-max_chars:]


def consolidate_today() -> Path:
    ensure_project_dirs()
    diary = read_diary()
    out = MEMORY_DIR / "medium_term" / f"daily_summary_{today_key()}.md"
    if not diary.strip():
        out.write_text(f"# Daily Summary {today_key()}\n\nNo diary entries yet.\n", encoding="utf-8")
        return out

    lines = [line.strip() for line in diary.splitlines() if line.strip()]
    user_lines = [line for line in lines if not line.startswith("#") and not line.startswith("##")]
    summary = [
        f"# Daily Summary {today_key()}",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Raw Signals",
        "",
    ]
    for line in user_lines[-80:]:
        summary.append(f"- {line}")
    summary.extend(
        [
            "",
            "## Candidate Memories",
            "",
            "- Review this summary and promote stable facts to long-term memory when confirmed.",
        ]
    )
    out.write_text("\n".join(summary) + "\n", encoding="utf-8")
    return out


def remember_fact(text: str) -> Path:
    stamp = datetime.now().isoformat(timespec="seconds")
    return append_memory_file("medium_term", "remembered_facts.md", f"- {stamp}: {text}")
