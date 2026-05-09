from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs
from memory.diary_manager import diary_path, read_diary, today_key
from dream.diary_consolidator import consolidate


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
    sandro_core = read_memory_file("long_term", "sandro_core_memory.md").strip()
    if sandro_core:
        pieces.append(f"## memory/long_term/sandro_core_memory.md\n{sandro_core[:8000]}")
        pieces.append(f"## memory/long_term/sandro_core_memory.md resumo prioritario\n{sandro_core[:3500]}")
    for rel in (
        ("long_term", "eve_operational_capabilities.md"),
        ("long_term", "eve_constitution.md"),
        ("long_term", "eve_mission.md"),
        ("personality", "core_identity.md"),
        ("personality", "soul.md"),
        ("personality", "identity.md"),
        ("personality", "values.md"),
        ("personality", "evolving_preferences.md"),
        ("personality", "helix_lore_distillation.md"),
    ):
        text = read_memory_file(*rel).strip()
        if text:
            pieces.append(f"## memory/{rel[0]}/{rel[1]}\n{text}")
    bundle = "\n\n".join(pieces)
    return bundle[-max_chars:]


def consolidate_today() -> Path:
    return consolidate(today_key())


def remember_fact(text: str) -> Path:
    stamp = datetime.now().isoformat(timespec="seconds")
    return append_memory_file("medium_term", "remembered_facts.md", f"- {stamp}: {text}")
