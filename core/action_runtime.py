from __future__ import annotations

import json
from typing import Any, Callable

from memory.daily_transcripts import append_transcript
from security.audit_log import log_event


Handler = Callable[[dict[str, Any]], dict[str, Any]]


def console_action(message: str) -> None:
    print(f"[Eve action] {message}")


FAILURE_STATUSES = {
    "failed",
    "failed_tests",
    "partial",
    "needs_confirmation",
    "needs_review",
    "needs_human_review",
    "blocked",
    "text_too_long",
    "composer_not_verified",
    "post_button_not_found",
}


def _nested_failure(value: Any, path: str = "result") -> dict[str, str] | None:
    if isinstance(value, dict):
        status = value.get("status")
        if status in FAILURE_STATUSES:
            reason = value.get("reason") or value.get("error") or status
            return {"path": path, "status": str(status), "reason": str(reason)}
        verification = value.get("verification")
        if isinstance(verification, dict) and not verification.get("ok", True):
            reason = verification.get("reason") or verification.get("rule") or "verification failed"
            return {"path": f"{path}.verification", "status": "verification_failed", "reason": str(reason)}
        for key, nested in value.items():
            found = _nested_failure(nested, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found = _nested_failure(item, f"{path}[{index}]")
            if found:
                return found
    return None


def verify_tool_result(tool: str, result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        return {"ok": False, "status": "failed", "reason": result.get("error") or "tool returned ok=false"}
    payload = result.get("result")
    if isinstance(payload, dict):
        if payload.get("status") in FAILURE_STATUSES:
            return {"ok": False, "status": payload.get("status"), "reason": payload.get("reason") or payload.get("status")}
        verification = payload.get("verification")
        if isinstance(verification, dict) and not verification.get("ok", True):
            return {"ok": False, "status": "verification_failed", "reason": verification.get("rule") or "verification failed"}
        if "requested" in payload and "confirmed" in payload and int(payload.get("confirmed") or 0) < int(payload.get("requested") or 0):
            return {"ok": False, "status": "count_mismatch", "reason": "confirmed count lower than requested count"}
        nested = _nested_failure(payload)
        if nested:
            return {
                "ok": False,
                "status": nested["status"],
                "reason": f"{nested['path']}: {nested['reason']}",
            }
    return {"ok": True, "status": "verified", "reason": "generic result check passed"}


def run_tool_with_runtime(tool: str, args: dict[str, Any], handler: Handler, *, max_attempts: int | None = None) -> dict[str, Any]:
    attempts = max(1, int(max_attempts or args.get("_max_attempts") or 1))
    last_result: dict[str, Any] | None = None
    history = []
    for attempt in range(1, attempts + 1):
        console_action(f"tool={tool} attempt={attempt}/{attempts} args={json.dumps(args, ensure_ascii=False)[:800]}")
        append_transcript("actions", "tool_start", {"tool": tool, "args": args, "attempt": attempt, "attempts": attempts})
        result = handler(args)
        verification = verify_tool_result(tool, result)
        result["verification"] = verification
        history.append({"attempt": attempt, "verification": verification})
        append_transcript("tools", "tool_result", {"tool": tool, "args": args, "result": result, "attempt": attempt})
        append_transcript("actions", "tool_verification", {"tool": tool, "verification": verification, "attempt": attempt})
        console_action(f"tool={tool} result_ok={result.get('ok')} verification={verification['status']}")
        last_result = result
        if verification["ok"]:
            break
        if attempt < attempts:
            console_action(f"tool={tool} retrying_after={verification['reason']}")
    assert last_result is not None
    last_result.setdefault("runtime", {})
    last_result["runtime"].update({"attempts": len(history), "history": history})
    if not last_result["verification"]["ok"]:
        append_transcript("errors", "tool_verification_failed", {"tool": tool, "args": args, "result": last_result})
        log_event("tool_verification_failed", {"tool": tool, "verification": last_result["verification"]})
    return last_result
