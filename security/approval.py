from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LOGS_DIR, ensure_project_dirs
from security.audit_log import log_event


def approval_log_path() -> Path:
    ensure_project_dirs()
    return LOGS_DIR / "approvals" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"


def request_approval(action: str, reason: str, risk: str, details: dict) -> dict:
    request = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "action": action,
        "reason": reason,
        "risk": risk,
        "details": details,
        "status": "requested",
    }
    with approval_log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(request, ensure_ascii=False) + "\n")
    log_event("approval_requested", request)
    return request


def approval_prompt(request: dict) -> str:
    return (
        "APROVACAO NECESSARIA\n"
        f"Acao: {request['action']}\n"
        f"Motivo: {request['reason']}\n"
        f"Risco: {request['risk']}\n"
        f"Detalhes: {json.dumps(request['details'], ensure_ascii=False)}\n"
        "Repete o comando com --aprovar se quiseres autorizar."
    )
