from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import LAB_DIR, ensure_project_dirs
from memory.errors.error_memory import recent_errors
from autonomy.capability_roadmap import capability_audit
from security.audit_log import log_event


def improvement_candidate_to_lab_candidate(candidate: dict) -> Path:
    return propose_improvement(
        str(candidate.get("source") or "autonomous"),
        str(candidate.get("affected_point_id") or candidate.get("hypothesis") or "system"),
        str(candidate.get("hypothesis") or "Improve Eve capability"),
        str(candidate.get("risk") or "low"),
    )


def improvement_candidate_to_patch_plan(candidate: dict) -> dict:
    return {
        "source": candidate.get("source", "unknown"),
        "affected_point_id": candidate.get("affected_point_id"),
        "files_to_change": candidate.get("files_to_change", []),
        "tests_required": candidate.get("tests_required", ["python -m pytest tests/test_core.py -q"]),
        "rollback": "restore git diff or backup created by verified_self_update",
        "risk": candidate.get("risk", "low"),
    }


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


def plan_autonomous_system_improvements(*, target_score: float = 8.5, max_items: int = 3) -> dict:
    audit = capability_audit()
    planned: list[dict] = []
    for point in sorted(audit["points"], key=lambda item: (item["score_10"], item["id"])):
        if len(planned) >= max_items:
            break
        if float(point["score_10"]) < target_score or point.get("goal_gaps"):
            path = propose_improvement(
                f"capability_{point['id']}",
                point["title"],
                f"Hardening necessario: score={point['score_10']} gaps={', '.join(point.get('goal_gaps') or []) or 'quality headroom'}",
                "low",
            )
            planned.append({"kind": "capability", "point": point["id"], "path": str(path), "score_10": point["score_10"]})
    for err_path in propose_from_recent_errors()[: max(0, max_items - len(planned))]:
        planned.append({"kind": "error", "path": str(err_path)})
    return {"target_score": target_score, "planned": planned, "count": len(planned), "audit_summary": audit["summary"]}
