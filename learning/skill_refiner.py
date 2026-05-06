from __future__ import annotations

import json
from pathlib import Path

from core.paths import SKILLS_DIR, ensure_project_dirs
from self_improvement.rollback_manager import backup_file


def add_skill_note(skill_ref: str, note: str) -> Path:
    ensure_project_dirs()
    path = SKILLS_DIR / f"{skill_ref}.json" if "/" in skill_ref else next(SKILLS_DIR.glob(f"*/{skill_ref}.json"))
    backup_file(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("notes", []).append(note)
    data["status"] = data.get("status", "draft")
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
