from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core.paths import SKILLS_DIR, ensure_project_dirs
from security.audit_log import log_event


USAGE_PATH = SKILLS_DIR / ".usage.json"
ARCHIVE_DIR = SKILLS_DIR / ".archive"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_usage() -> dict[str, Any]:
    ensure_project_dirs()
    if not USAGE_PATH.exists():
        return {}
    try:
        return json.loads(USAGE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_usage(data: dict[str, Any]) -> Path:
    USAGE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return USAGE_PATH


def record_skill_usage(skill_ref: str, *, event: str = "run") -> dict[str, Any]:
    data = _load_usage()
    row = data.setdefault(skill_ref, {"use_count": 0, "view_count": 0, "state": "active", "pinned": False})
    if event == "view":
        row["view_count"] = int(row.get("view_count") or 0) + 1
    else:
        row["use_count"] = int(row.get("use_count") or 0) + 1
    row["last_activity_at"] = now_iso()
    _save_usage(data)
    return row


def curate_skills(*, stale_after_days: int = 30, archive_after_days: int = 90, dry_run: bool = True) -> dict[str, Any]:
    ensure_project_dirs()
    usage = _load_usage()
    now = datetime.now(timezone.utc)
    actions = []
    for root in (SKILLS_DIR / "draft", SKILLS_DIR / "trusted"):
        for path in root.glob("*.json"):
            ref = f"{root.name}/{path.stem}"
            row = usage.setdefault(ref, {"use_count": 0, "view_count": 0, "state": "active", "pinned": False})
            if row.get("pinned"):
                continue
            last_text = row.get("last_activity_at") or path.stat().st_mtime
            last = (
                datetime.fromisoformat(str(last_text).replace("Z", "+00:00"))
                if isinstance(last_text, str)
                else datetime.fromtimestamp(float(last_text), timezone.utc)
            )
            age = now - last
            if age >= timedelta(days=archive_after_days):
                action = {"skill": ref, "action": "archive", "dry_run": dry_run}
                if not dry_run:
                    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(path), str(ARCHIVE_DIR / path.name))
                    row["state"] = "archived"
                actions.append(action)
            elif age >= timedelta(days=stale_after_days):
                row["state"] = "stale"
                actions.append({"skill": ref, "action": "mark_stale", "dry_run": dry_run})
    _save_usage(usage)
    result = {"actions": actions, "usage_path": str(USAGE_PATH)}
    log_event("skill_curator_run", result)
    return result

