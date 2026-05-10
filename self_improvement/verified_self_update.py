from __future__ import annotations

import json
import py_compile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.paths import BACKUPS_DIR, EVE_ROOT, LAB_DIR, ensure_project_dirs
from security.audit_log import log_event
from security.permission_manager import check_action
from self_improvement.rollback_manager import backup_file


RepairFunc = Callable[[str, dict[str, Any]], str]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _candidate_dir() -> Path:
    ensure_project_dirs()
    path = LAB_DIR / "candidate_improvements" / "verified_updates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_target(path: str) -> Path:
    target = (EVE_ROOT / path).resolve()
    root = EVE_ROOT.resolve()
    if target != root and root not in target.parents:
        raise PermissionError("Verified self-update so pode alterar ficheiros dentro de D:\\Eve")
    return target


def _write_candidate(target: Path, content: str, attempt: int) -> Path:
    suffix = target.suffix or ".txt"
    candidate = _candidate_dir() / f"{target.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}_attempt{attempt}{suffix}"
    candidate.write_text(content, encoding="utf-8")
    return candidate


def _run_candidate_tests(candidate: Path, tests: list[str]) -> dict[str, Any]:
    results = []
    for test in tests:
        if test == "py_compile_candidate":
            try:
                py_compile.compile(str(candidate), doraise=True)
                results.append({"name": test, "passed": True, "stdout": "", "stderr": ""})
            except py_compile.PyCompileError as exc:
                results.append({"name": test, "passed": False, "stdout": "", "stderr": str(exc)})
        else:
            results.append({"name": test, "passed": False, "stdout": "", "stderr": f"Teste desconhecido: {test}"})
    passed = all(item["passed"] for item in results)
    return {"passed": passed, "results": results, "candidate": str(candidate)}


def _write_report(payload: dict[str, Any]) -> Path:
    ensure_project_dirs()
    path = BACKUPS_DIR / "tmp" / f"verified_self_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def verified_core_update(
    path: str,
    proposed_content: str,
    *,
    tests: list[str] | None = None,
    repair_func: RepairFunc | None = None,
    max_attempts: int = 1,
    approved: bool = False,
) -> dict[str, Any]:
    decision = check_action("self_modify_core", approved=approved)
    if not decision.allowed:
        return {
            "status": "blocked",
            "applied": False,
            "allowed": False,
            "reason": decision.reason,
            "requires_approval": decision.requires_approval,
        }

    target = _resolve_target(path)
    test_list = tests or (["py_compile_candidate"] if target.suffix == ".py" else [])
    content = proposed_content
    attempts: list[dict[str, Any]] = []
    max_attempts = max(1, int(max_attempts))

    for attempt in range(1, max_attempts + 1):
        candidate = _write_candidate(target, content, attempt)
        test_result = _run_candidate_tests(candidate, test_list) if test_list else {"passed": True, "results": [], "candidate": str(candidate)}
        attempts.append({"attempt": attempt, "candidate": str(candidate), "tests": test_result})
        if test_result["passed"]:
            backup = backup_file(target, "verified_self_update") if target.exists() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            result = {
                "status": "applied",
                "applied": True,
                "allowed": True,
                "target": str(target),
                "backup": str(backup) if backup else None,
                "attempts": attempt,
                "tests": test_result,
                "history": attempts,
                "updated_at": now_iso(),
            }
            result["report"] = str(_write_report(result))
            log_event("verified_self_update_applied", result)
            return result
        if repair_func is None or attempt == max_attempts:
            break
        content = repair_func(content, test_result)

    result = {
        "status": "failed_tests",
        "applied": False,
        "allowed": True,
        "target": str(target),
        "attempts": len(attempts),
        "tests": attempts[-1]["tests"] if attempts else None,
        "history": attempts,
        "updated_at": now_iso(),
    }
    result["report"] = str(_write_report(result))
    log_event("verified_self_update_failed", result)
    return result
