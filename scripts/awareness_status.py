from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.awareness_engine import build_self_state, write_self_state
from core.heartbeat_tracker import estimate_uptime, read_last_heartbeat


def main() -> int:
    state = build_self_state()
    write_self_state(state)
    session = (state.get("session") or {}).get("current_session") or {}
    rollover = state.get("rollover") or {}
    latest_handoff = (state.get("session") or {}).get("latest_handoff") or {}
    summary = {
        "pc": state.get("pc_identity", {}).get("pc_role"),
        "eve_root": state.get("pc_identity", {}).get("eve_root"),
        "webui_ok": state.get("health_summary", {}).get("webui_ok"),
        "telegram_ok": state.get("health_summary", {}).get("telegram_running"),
        "ollama_ok": state.get("health_summary", {}).get("ollama_ok"),
        "vector_db_ok": bool((state.get("vector") or {}).get("chroma_exists")),
        "current_session_id": session.get("session_id"),
        "current_memory_day": session.get("memory_day"),
        "latest_handoff_exists": latest_handoff.get("exists"),
        "latest_handoff_size": latest_handoff.get("size"),
        "last_rollover": ((rollover.get("last_rollover") or {}).get("rollup") or {}).get("path"),
        "last_dream": ((rollover.get("last_rollover") or {}).get("dream_report") or {}).get("path"),
        "open_errors": (state.get("errors") or {}).get("open_errors"),
        "git_branch": (state.get("git") or {}).get("branch"),
        "git_dirty": (state.get("git") or {}).get("dirty"),
        "daily_rollover_task": ((state.get("scheduled_tasks") or {}).get("daily_rollover") or {}).get("state"),
        "uptime_estimate": estimate_uptime(),
        "last_heartbeat": read_last_heartbeat(),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
