from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LAB_DIR, ensure_project_dirs
from memory.errors.error_memory import recent_errors
from security.audit_log import log_event


def propose_improvement(area: str, problem: str, proposal: str, risk: str = "low") -> Path:
    ensure_project_dirs()
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in f"{area}_{problem}".lower()).strip("_")
    path = LAB_DIR / "candidate_improvements" / f"{safe}.json"
    payload = {
        "area": area,
        "problem": problem,
        "proposal": proposal,
        "risk": risk,
        "status": "proposed",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "manual_or_rsi",
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log_event("improvement_proposed", {"path": str(path), "risk": risk})
    return path


def propose_from_recent_errors() -> list[Path]:
    proposals = []
    for err in recent_errors(limit=5):
        proposals.append(
            propose_improvement(
                "error_handling",
                err.get("error_type", "unknown_error"),
                f"Criar licao ou teste para: {err.get('error_text', '')[:300]}",
                "low",
            )
        )
    return proposals
