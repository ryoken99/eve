from __future__ import annotations

import json
from datetime import datetime, timezone

from core.paths import LOGS_DIR, ensure_project_dirs
from memory.errors.error_memory import recent_errors
from autonomy.scheduler import list_scheduled_tasks


def decide_proactive_actions() -> dict:
    ensure_project_dirs()
    actions = []
    errors = recent_errors(limit=3)
    if errors:
        actions.append({"kind": "error_review", "message": "resumir erros recentes e criar licoes adaptativas", "risk": "low", "notify_sandro": True})
    if not list_scheduled_tasks():
        actions.append({"kind": "schedule_hygiene", "message": "criar agenda local para consolidacao, sonho e pesquisa tecnologica", "risk": "low", "notify_sandro": False})
    actions.append({"kind": "continuity", "message": "manter diario e estado vivo atualizados", "risk": "low", "notify_sandro": False})
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "actions": actions,
        "count": len(actions),
    }
    path = LOGS_DIR / "autonomy" / "proactive_decisions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    result["log_path"] = str(path)
    return result


def propose_low_risk_actions() -> list[str]:
    return [item["message"] for item in decide_proactive_actions()["actions"]]
