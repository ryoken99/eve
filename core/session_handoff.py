from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.mission_control import list_missions
from core.paths import STATE_DIR, ensure_project_dirs
from core.session_store import count_session_messages, recent_session_messages


HANDOFF_DIR = STATE_DIR / "session_handoffs"
ACTIVE_SESSION_PATH = STATE_DIR / "current_session.json"
ACTIVE_HANDOFF_PATH = HANDOFF_DIR / "active_handoff.json"
ACTIVE_HANDOFF_MD = HANDOFF_DIR / "active_handoff.md"
DEFAULT_SESSION_ID = "main"
WARNING_MESSAGES = 80
ROTATE_MESSAGES = 120


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure() -> None:
    ensure_project_dirs()
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)


def current_session_id() -> str:
    _ensure()
    if not ACTIVE_SESSION_PATH.exists():
        set_current_session(DEFAULT_SESSION_ID, reason="initial default")
        return DEFAULT_SESSION_ID
    try:
        data = json.loads(ACTIVE_SESSION_PATH.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_SESSION_ID
    return str(data.get("session_id") or DEFAULT_SESSION_ID)


def set_current_session(session_id: str, *, reason: str = "") -> dict[str, Any]:
    _ensure()
    clean = session_id.strip() or DEFAULT_SESSION_ID
    payload = {"session_id": clean, "changed_at": now_iso(), "reason": reason}
    ACTIVE_SESSION_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def context_status(session_id: str | None = None) -> dict[str, Any]:
    sid = session_id or current_session_id()
    messages = count_session_messages(sid)
    if messages >= ROTATE_MESSAGES:
        level = "rotate"
    elif messages >= WARNING_MESSAGES:
        level = "warning"
    else:
        level = "ok"
    return {
        "session_id": sid,
        "messages": messages,
        "warning_messages": WARNING_MESSAGES,
        "rotate_messages": ROTATE_MESSAGES,
        "level": level,
        "should_checkpoint": level in {"warning", "rotate"},
        "should_rotate": level == "rotate",
    }


def _compact_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = []
    for item in messages:
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        compact.append(
            {
                "role": item.get("role", "unknown"),
                "created_at": item.get("created_at"),
                "content": content[:1400],
            }
        )
    return compact


def _markdown_handoff(handoff: dict[str, Any]) -> str:
    lines = [
        "# Eve Session Handoff",
        "",
        f"- Session: `{handoff['session_id']}`",
        f"- Created: `{handoff['created_at']}`",
        f"- Reason: {handoff['reason']}",
        f"- Message count: {handoff['context_status']['messages']}",
        "",
        "## Active Missions",
    ]
    missions = handoff.get("active_missions") or []
    if missions:
        for mission in missions:
            lines.append(f"- `{mission['id']}` [{mission['status']}]: {mission['objective']} | next: {mission.get('next_step')}")
    else:
        lines.append("- None")
    lines.extend(["", "## Recent Thread"])
    for item in handoff.get("recent_messages", []):
        role = item.get("role", "unknown")
        content = str(item.get("content") or "").replace("\n", " ")
        lines.append(f"- **{role}**: {content[:500]}")
    lines.extend(
        [
            "",
            "## Resume Instruction",
            "Continue from this handoff. Use tools directly when needed. Do not ask Sandro to type slash commands if an internal tool exists.",
        ]
    )
    return "\n".join(lines) + "\n"


def create_session_checkpoint(
    session_id: str | None = None,
    *,
    reason: str = "manual checkpoint",
    recent_limit: int = 40,
) -> dict[str, Any]:
    _ensure()
    sid = session_id or current_session_id()
    handoff = {
        "id": f"handoff_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
        "session_id": sid,
        "created_at": now_iso(),
        "reason": reason,
        "context_status": context_status(sid),
        "active_missions": list_missions(status="running")[:10] + list_missions(status="proposed")[:10],
        "recent_messages": _compact_messages(recent_session_messages(sid, limit=recent_limit)),
    }
    json_path = HANDOFF_DIR / f"{handoff['id']}.json"
    md_path = HANDOFF_DIR / f"{handoff['id']}.md"
    json_path.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown_handoff(handoff), encoding="utf-8")
    ACTIVE_HANDOFF_PATH.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
    ACTIVE_HANDOFF_MD.write_text(_markdown_handoff(handoff), encoding="utf-8")
    handoff["paths"] = {"json": str(json_path), "markdown": str(md_path), "active_json": str(ACTIVE_HANDOFF_PATH)}
    return handoff


def load_active_handoff() -> dict[str, Any] | None:
    _ensure()
    if not ACTIVE_HANDOFF_PATH.exists():
        return None
    try:
        return json.loads(ACTIVE_HANDOFF_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def format_active_handoff(max_chars: int = 7000) -> str:
    _ensure()
    if not ACTIVE_HANDOFF_MD.exists():
        return ""
    return ACTIVE_HANDOFF_MD.read_text(encoding="utf-8", errors="replace")[:max_chars]


def rotate_session(*, reason: str = "context rotation", new_session_id: str | None = None) -> dict[str, Any]:
    old_session = current_session_id()
    checkpoint = create_session_checkpoint(old_session, reason=reason)
    new_session = new_session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    state = set_current_session(new_session, reason=reason)
    return {"previous_session_id": old_session, "current_session_id": new_session, "checkpoint": checkpoint, "state": state}
