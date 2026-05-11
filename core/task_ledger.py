from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.paths import STATE_DIR, ensure_project_dirs


TASK_LEDGER_PATH = STATE_DIR / "task_ledger.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_task_event(event: str, payload: dict) -> dict:
    ensure_project_dirs()
    row = {"timestamp": _now(), "event": event, **payload}
    with TASK_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def start_tool_task(tool: str, args: dict, *, source: str = "eve_llm") -> str:
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    append_task_event("task_started", {"task_id": task_id, "source": source, "tool": tool, "args": args, "status": "running"})
    return task_id


def finish_tool_task(task_id: str, result: dict) -> None:
    verification = result.get("verification") if isinstance(result.get("verification"), dict) else {}
    verified = bool(verification.get("ok", result.get("ok", False)))
    status = "done" if result.get("ok") and verified else "failed"
    append_task_event(
        "task_finished",
        {
            "task_id": task_id,
            "tool": result.get("tool"),
            "status": status,
            "verified": verified,
            "verification": verification,
            "result": result,
        },
    )

