from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.paths import LOGS_DIR, STATE_DIR, ensure_project_dirs


SESSIONS_PATH = STATE_DIR / "admin_sessions.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass
class AdminSession:
    session_id: str
    reason: str
    created_at: str
    expires_at: str
    allowed_commands: list[str]
    active: bool = True


def _load() -> dict[str, dict]:
    ensure_project_dirs()
    if not SESSIONS_PATH.exists():
        return {}
    try:
        return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(rows: dict[str, dict]) -> Path:
    SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return SESSIONS_PATH


def _log(event: str, payload: dict) -> Path:
    path = LOGS_DIR / "admin_actions" / f"{_now().strftime('%Y-%m-%d')}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"timestamp": _iso(_now()), "event": event, **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def create_admin_session(reason: str, duration_minutes: int, allowed_commands: list[str]) -> dict:
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be positive")
    if not allowed_commands:
        raise ValueError("allowed_commands cannot be empty")
    created = _now()
    session = AdminSession(
        session_id=f"admin-{created.strftime('%Y%m%d%H%M%S')}",
        reason=reason,
        created_at=_iso(created),
        expires_at=_iso(created + timedelta(minutes=duration_minutes)),
        allowed_commands=allowed_commands,
    )
    rows = _load()
    rows[session.session_id] = asdict(session)
    _save(rows)
    _log("admin_session_created", asdict(session))
    return asdict(session)


def list_admin_sessions(*, include_expired: bool = False) -> list[dict]:
    rows = _load()
    result = []
    for session in rows.values():
        expired = _parse(session["expires_at"]) <= _now()
        if expired and not include_expired:
            continue
        result.append({**session, "expired": expired})
    return result


def expire_admin_session(session_id: str) -> dict:
    rows = _load()
    session = rows.get(session_id)
    if not session:
        return {"allowed": False, "reason": "admin session not found", "session_id": session_id}
    session["active"] = False
    rows[session_id] = session
    _save(rows)
    _log("admin_session_expired", {"session_id": session_id})
    return {"allowed": True, "session_id": session_id, "active": False}


def validate_admin_session(session_id: str | None, command: str) -> dict:
    if not session_id:
        return {"allowed": False, "reason": "admin session required"}
    session = _load().get(session_id)
    if not session:
        return {"allowed": False, "reason": "admin session not found", "session_id": session_id}
    if not session.get("active", True):
        return {"allowed": False, "reason": "admin session inactive", "session_id": session_id}
    if _parse(session["expires_at"]) <= _now():
        return {"allowed": False, "reason": "admin session expired", "session_id": session_id}
    allowed = any(fnmatch.fnmatch(command.lower(), pattern.lower()) for pattern in session.get("allowed_commands", []))
    if not allowed:
        _log("admin_session_command_blocked", {"session_id": session_id, "command": command})
        return {"allowed": False, "reason": "command outside admin allowlist", "session_id": session_id}
    _log("admin_session_command_allowed", {"session_id": session_id, "command": command})
    return {"allowed": True, "session_id": session_id, "reason": session.get("reason", "")}
