from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.paths import MEMORY_DIR, SKILLS_DIR, ensure_project_dirs
from learning.adaptive_learning import record_adaptive_lesson, record_skill_failure
from learning.skill_manager import now_iso, promote_skill, run_skill
from security.audit_log import log_event
from self_improvement.rollback_manager import backup_file


ATTEMPT_LOG = MEMORY_DIR / "procedural" / "skill_learning_loop.jsonl"
FAILURE_STATUSES = {
    "error",
    "failed",
    "needs_review",
    "needs_human_review",
    "composer_not_verified",
    "post_button_not_found",
}


@dataclass
class LearningLoopResult:
    skill_ref: str
    status: str
    attempts: list[dict[str, Any]]
    promoted_to: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "skill_ref": self.skill_ref,
            "status": self.status,
            "attempts": self.attempts,
            "promoted_to": self.promoted_to,
        }


def _skill_path(skill_ref: str) -> Path:
    ensure_project_dirs()
    if "/" in skill_ref:
        path = SKILLS_DIR / f"{skill_ref}.json"
        if not path.exists():
            raise FileNotFoundError(f"Skill nao encontrada: {skill_ref}")
        return path
    candidates = list(SKILLS_DIR.glob(f"*/{skill_ref}.json"))
    if not candidates:
        raise FileNotFoundError(f"Skill nao encontrada: {skill_ref}")
    return candidates[0]


def _read_skill(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_skill(path: Path, skill: dict[str, Any], reason: str) -> Path:
    backup_file(path, reason)
    skill["updated_at"] = now_iso()
    path.write_text(json.dumps(skill, indent=2, ensure_ascii=False), encoding="utf-8")
    log_event("skill_learning_loop_skill_updated", {"path": str(path), "reason": reason})
    return path


def _contains_failure_status(value: Any) -> bool:
    if isinstance(value, dict):
        status = str(value.get("status", "")).lower()
        if status in FAILURE_STATUSES:
            return True
        return any(_contains_failure_status(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_failure_status(item) for item in value)
    return False


def skill_result_successful(result: dict[str, Any]) -> bool:
    return not _contains_failure_status(result)


def _write_attempt(entry: dict[str, Any]) -> Path:
    ensure_project_dirs()
    ATTEMPT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ATTEMPT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log_event("skill_learning_loop_attempt", entry)
    return ATTEMPT_LOG


def _matching_step_indexes(skill: dict[str, Any], correction: dict[str, Any]) -> list[int]:
    steps = skill.get("steps") or []
    if "step_index" in correction:
        index = int(correction["step_index"])
        if index < 0 or index >= len(steps):
            raise IndexError(f"step_index fora de alcance: {index}")
        return [index]
    action = correction.get("match_action")
    if action:
        matches = [index for index, step in enumerate(steps) if step.get("action") == action]
        if not matches:
            raise ValueError(f"Nenhum passo encontrado com action={action}")
        return matches
    raise ValueError("Correcao de passo precisa de step_index ou match_action")


def apply_skill_correction(skill_ref: str, correction: dict[str, Any]) -> dict[str, Any]:
    path = _skill_path(skill_ref)
    skill = _read_skill(path)
    action = correction.get("action")
    if action == "add_note":
        skill.setdefault("notes", []).append(str(correction["note"]))
    elif action == "set_status":
        skill["status"] = str(correction["status"])
    elif action == "set_step_field":
        for index in _matching_step_indexes(skill, correction):
            skill["steps"][index][str(correction["field"])] = correction.get("value")
    elif action == "remove_step_field":
        for index in _matching_step_indexes(skill, correction):
            skill["steps"][index].pop(str(correction["field"]), None)
    elif action == "append_step":
        skill.setdefault("steps", []).append(correction["step"])
    elif action == "replace_step":
        indexes = _matching_step_indexes(skill, correction)
        if len(indexes) != 1:
            raise ValueError("replace_step exige um unico passo alvo")
        skill["steps"][indexes[0]] = correction["step"]
    elif action == "remove_step":
        for index in sorted(_matching_step_indexes(skill, correction), reverse=True):
            del skill["steps"][index]
    else:
        raise ValueError(f"Correcao desconhecida: {action}")
    _write_skill(path, skill, f"learning loop correction: {action}")
    payload = {"skill_ref": skill_ref, "correction": correction, "path": str(path)}
    log_event("skill_learning_loop_correction_applied", payload)
    return payload


def run_skill_learning_loop(
    skill_ref: str,
    *,
    args: dict[str, Any] | None = None,
    approved: bool = False,
    max_attempts: int = 3,
    corrections: list[dict[str, Any]] | None = None,
    promote_on_success: bool = False,
    success_note: str | None = None,
) -> dict[str, Any]:
    if max_attempts < 1:
        raise ValueError("max_attempts tem de ser pelo menos 1")
    corrections = corrections or []
    attempts: list[dict[str, Any]] = []
    last_error = ""
    for attempt_number in range(1, max_attempts + 1):
        try:
            result = run_skill(skill_ref, args=args, approved=approved)
            success = skill_result_successful(result)
            entry = {
                "timestamp": now_iso(),
                "skill_ref": skill_ref,
                "attempt": attempt_number,
                "success": success,
                "result": result,
            }
            attempts.append(entry)
            _write_attempt(entry)
            if success:
                note = success_note or "Skill passed the autonomous learning loop."
                record_adaptive_lesson(
                    skill_ref,
                    "Skill required iterative execution and verification.",
                    "The learning loop retried after corrections and accepted only a successful verification.",
                    note,
                )
                promoted_to = None
                if promote_on_success:
                    skill_path = _skill_path(skill_ref)
                    if skill_path.parent.name == "draft":
                        promoted_to = str(promote_skill(skill_path.stem))
                final = LearningLoopResult(skill_ref, "success", attempts, promoted_to)
                log_event("skill_learning_loop_completed", final.as_dict())
                return final.as_dict()
            last_error = "Skill result contained failure status."
            record_skill_failure(skill_ref, f"attempt_{attempt_number}", last_error, json.dumps(result, ensure_ascii=False))
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            entry = {
                "timestamp": now_iso(),
                "skill_ref": skill_ref,
                "attempt": attempt_number,
                "success": False,
                "error": last_error,
            }
            attempts.append(entry)
            _write_attempt(entry)
            record_skill_failure(skill_ref, f"attempt_{attempt_number}", last_error)
        correction_index = attempt_number - 1
        if correction_index < len(corrections):
            applied = apply_skill_correction(skill_ref, corrections[correction_index])
            attempts[-1]["correction_applied"] = applied
        elif attempt_number < max_attempts:
            attempts[-1]["correction_applied"] = None
            break
    final = LearningLoopResult(skill_ref, "failed", attempts)
    log_event("skill_learning_loop_failed", {**final.as_dict(), "last_error": last_error})
    return final.as_dict()
