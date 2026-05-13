from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from computer.action_router import perform_ui_action
from core.paths import LOGS_DIR, ensure_project_dirs


def _log_task(row: dict) -> Path:
    ensure_project_dirs()
    path = LOGS_DIR / "ui_actions" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def run_ui_task(target_app: str, steps: list[dict], *, confirmed: bool = False) -> dict:
    results = []
    for index, step in enumerate(steps, start=1):
        result = perform_ui_action(
            target_app,
            step["action"],
            step.get("selector", {}),
            step.get("text"),
            confirmed=confirmed or bool(step.get("confirmed")),
            expected_change=step.get("expected_change"),
        )
        results.append({"step": index, **result})
        if not result.get("ok"):
            break
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "target_app": target_app,
        "completed": len(results) == len(steps) and all(row.get("ok") for row in results),
        "results": results,
    }
    payload["log_path"] = str(_log_task(payload))
    return payload
