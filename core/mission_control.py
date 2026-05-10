from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.paths import STATE_DIR, ensure_project_dirs


MISSION_STATUSES = {"draft", "proposed", "running", "paused", "blocked", "done", "failed"}
STEP_STATUSES = {"pending", "running", "done", "blocked", "failed", "skipped"}


def missions_dir() -> Path:
    ensure_project_dirs()
    path = STATE_DIR / "missions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "mission"


def mission_path(mission_id: str) -> Path:
    return missions_dir() / f"{mission_id}.json"


def next_step(mission: dict) -> dict | None:
    for step in mission.get("steps", []):
        if step.get("status") in {"pending", "running", "blocked", "failed"}:
            return {
                "index": step["index"],
                "description": step["description"],
                "status": step["status"],
            }
    return None


def _save(mission: dict) -> dict:
    mission["updated_at"] = now_iso()
    mission["next_step"] = next_step(mission)
    mission_path(mission["id"]).write_text(json.dumps(mission, indent=2, ensure_ascii=False), encoding="utf-8")
    return mission


def create_mission(
    objective: str,
    *,
    plan: list[str] | None = None,
    permissions: list[str] | None = None,
    status: str = "draft",
    source: str = "manual",
) -> dict:
    if status not in MISSION_STATUSES:
        raise ValueError(f"estado de missao invalido: {status}")
    clean_plan = [item.strip() for item in (plan or []) if item.strip()]
    mission_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify(objective)}-{uuid.uuid4().hex[:6]}"
    mission = {
        "id": mission_id,
        "objective": objective.strip(),
        "status": status,
        "source": source,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "permissions": permissions or [],
        "steps": [
            {"index": index, "description": description, "status": "pending", "notes": []}
            for index, description in enumerate(clean_plan)
        ],
        "logs": [],
        "checkpoints": [],
        "next_step": None,
    }
    return _save(mission)


def load_mission(mission_id: str) -> dict:
    path = mission_path(mission_id)
    if not path.exists():
        raise FileNotFoundError(f"missao nao encontrada: {mission_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_missions(status: str | None = None, *, limit: int | None = None) -> list[dict]:
    rows = []
    for path in sorted(missions_dir().glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        mission = json.loads(path.read_text(encoding="utf-8"))
        if status and mission.get("status") != status:
            continue
        rows.append(
            {
                "id": mission["id"],
                "objective": mission["objective"],
                "status": mission["status"],
                "updated_at": mission["updated_at"],
                "next_step": mission.get("next_step"),
            }
        )
        if limit is not None and len(rows) >= int(limit):
            break
    return rows


def append_mission_log(mission_id: str, actor: str, message: str, *, data: dict | None = None) -> dict:
    mission = load_mission(mission_id)
    mission.setdefault("logs", []).append(
        {
            "timestamp": now_iso(),
            "actor": actor,
            "message": message,
            "data": data or {},
        }
    )
    return _save(mission)


def add_checkpoint(mission_id: str, name: str, data: dict | None = None) -> dict:
    mission = load_mission(mission_id)
    mission.setdefault("checkpoints", []).append(
        {
            "timestamp": now_iso(),
            "name": name,
            "data": data or {},
        }
    )
    return _save(mission)


def set_mission_status(mission_id: str, status: str, *, reason: str = "", actor: str = "system") -> dict:
    if status not in MISSION_STATUSES:
        raise ValueError(f"estado de missao invalido: {status}")
    mission = load_mission(mission_id)
    mission["status"] = status
    if reason:
        mission.setdefault("logs", []).append({"timestamp": now_iso(), "actor": actor, "message": reason, "data": {"status": status}})
    return _save(mission)


def update_step(mission_id: str, index: int, status: str, *, note: str = "", actor: str = "system") -> dict:
    if status not in STEP_STATUSES:
        raise ValueError(f"estado de passo invalido: {status}")
    mission = load_mission(mission_id)
    steps = mission.get("steps", [])
    if index < 0 or index >= len(steps):
        raise IndexError(f"passo fora de alcance: {index}")
    step = steps[index]
    step["status"] = status
    if note:
        step.setdefault("notes", []).append({"timestamp": now_iso(), "actor": actor, "note": note})
        mission.setdefault("logs", []).append({"timestamp": now_iso(), "actor": actor, "message": note, "data": {"step": index, "status": status}})
    if steps and all(item["status"] in {"done", "skipped"} for item in steps):
        mission["status"] = "done"
    elif mission["status"] == "draft" and status == "running":
        mission["status"] = "running"
    return _save(mission)


def resume_summary(mission_id: str) -> dict:
    mission = load_mission(mission_id)
    return {
        "id": mission["id"],
        "objective": mission["objective"],
        "status": mission["status"],
        "permissions": mission.get("permissions", []),
        "next_step": mission.get("next_step"),
        "last_log": (mission.get("logs") or [None])[-1],
        "last_checkpoint": (mission.get("checkpoints") or [None])[-1],
    }
