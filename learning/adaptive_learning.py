from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import MEMORY_DIR, ensure_project_dirs
from learning.lesson_extractor import extract_lesson
from security.audit_log import log_event


FAILURE_PATH = MEMORY_DIR / "procedural" / "adaptive_failures.jsonl"


def record_skill_failure(skill: str, step: str, error: str, observation: str = "") -> Path:
    ensure_project_dirs()
    FAILURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "skill": skill,
        "step": step,
        "error": error,
        "observation": observation,
        "status": "needs_review",
    }
    with FAILURE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log_event("skill_failure_recorded", entry)
    return FAILURE_PATH


def record_adaptive_lesson(skill: str, problem: str, fix: str, lesson: str) -> Path:
    path = extract_lesson(skill, problem, fix, lesson)
    log_event("adaptive_lesson_recorded", {"skill": skill, "path": str(path)})
    return path
