from __future__ import annotations

from pathlib import Path

from self_improvement.improvement_planner import propose_improvement
from self_improvement.patch_generator import write_patch_proposal
from self_improvement.sandbox_tester import run_python_compile
from security.audit_log import log_event


def run_improvement_pipeline(area: str, problem: str, proposal: str, patch_text: str = "") -> dict:
    candidate = propose_improvement(area, problem, proposal, "medium" if patch_text else "low")
    patch = None
    if patch_text:
        patch = write_patch_proposal(f"{area}_{problem}", proposal, patch_text)
    tests = run_python_compile(["main.py", "app/eve_codex.py"])
    result = {
        "candidate": str(candidate),
        "patch_proposal": str(patch) if patch else None,
        "tests": tests,
        "applied": False,
        "reason": "pipeline only stages proposals; core application remains explicit",
    }
    log_event("improvement_pipeline_run", result)
    return result
