from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVE_ROOT = Path(__file__).resolve().parents[1]
REQUEST_ROOT = EVE_ROOT / "memory" / "_processed" / "autonomy" / "codex_assistance"
POLICY_PATH = EVE_ROOT / "memory" / "_system" / "codex_tool_policy.yaml"


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def should_use_codex(change_plan: dict[str, Any], risk: str, failure_count: int = 0) -> dict[str, Any]:
    reasons = []
    if failure_count >= 2:
        reasons.append("tests_failed_twice")
    if risk in {"high", "critical"}:
        reasons.append("complex_or_high_risk")
    if change_plan.get("needs_second_opinion"):
        reasons.append("second_opinion_requested")
    return {
        "should_use_codex": bool(reasons),
        "reasons": reasons,
        "codex_required": False,
        "eve_remains_primary_agent": True,
    }


def create_codex_task_brief(change_plan: dict[str, Any]) -> str:
    return (
        "# Optional Codex Assistance Brief\n\n"
        "Eve remains the primary agent. Codex is optional tooling only.\n\n"
        f"Goal: {change_plan.get('goal', 'unknown')}\n"
        f"Risk: {change_plan.get('risk', 'unknown')}\n"
        f"Targets: {', '.join(change_plan.get('target_files', []))}\n\n"
        "Constraints:\n"
        "- Do not receive secrets or private memory dumps.\n"
        "- Do not push to GitHub.\n"
        "- Provide patch/review only; Eve decides final apply/test/rollback.\n"
    )


def record_codex_assistance_request(change_plan: dict[str, Any]) -> dict[str, Any]:
    REQUEST_ROOT.mkdir(parents=True, exist_ok=True)
    request_id = f"codex_assist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    brief = create_codex_task_brief(change_plan)
    path = REQUEST_ROOT / f"{request_id}.md"
    path.write_text(brief, encoding="utf-8")
    payload = {"request_id": request_id, "created_at": _now_iso(), "path": str(path), "status": "prepared_not_sent"}
    (REQUEST_ROOT / f"{request_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def import_codex_patch_for_review(path: str) -> dict[str, Any]:
    patch_path = Path(path)
    return {"exists": patch_path.exists(), "path": str(patch_path), "status": "review_required"}


def compare_eve_patch_with_codex_patch(eve_patch: str, codex_patch: str) -> dict[str, Any]:
    return {
        "eve_patch_chars": len(eve_patch or ""),
        "codex_patch_chars": len(codex_patch or ""),
        "requires_human_review": True,
        "eve_decides_final_apply": True,
    }
