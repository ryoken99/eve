from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import SKILLS_DIR, ensure_project_dirs


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_draft_skill(name: str, description: str, steps: list[dict], permissions: list[str] | None = None) -> Path:
    ensure_project_dirs()
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip().lower())
    path = SKILLS_DIR / "draft" / f"{safe_name}.json"
    payload = {
        "name": safe_name,
        "description": description,
        "risk_level": "low",
        "permissions": permissions or [],
        "steps": steps,
        "success_check": [],
        "version": 1,
        "status": "draft",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_skills(status: str | None = None) -> list[str]:
    ensure_project_dirs()
    roots = [SKILLS_DIR / status] if status else [p for p in SKILLS_DIR.iterdir() if p.is_dir()]
    found = []
    for root in roots:
        for path in root.glob("*.json"):
            found.append(f"{root.name}/{path.stem}")
    return sorted(found)
