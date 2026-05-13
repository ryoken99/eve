from __future__ import annotations

from self_improvement.change_registry import record_change
from self_improvement.rsi_evaluator import evaluate_rsi_candidate
from self_improvement.rsi_sandbox import sandbox_result


def run_improvement_cycle(candidate: dict, *, approved: bool = False) -> dict:
    sandbox = sandbox_result(candidate)
    evaluation = evaluate_rsi_candidate(candidate, approved=approved)
    applied = sandbox["sandbox_ok"] and evaluation["accepted"]
    record = record_change({"candidate": candidate, "sandbox": sandbox, "evaluation": evaluation, "applied": applied})
    return {"applied": applied, "sandbox": sandbox, "evaluation": evaluation, "record": record}
