from __future__ import annotations

from pathlib import Path

from core.paths import BACKUPS_DIR
from lab.experiment_runner import create_experiment
from self_improvement.improvement_planner import propose_from_recent_errors, propose_improvement
from self_improvement.sandbox_tester import run_python_compile


def run_controlled_rsi_cycle() -> dict:
    proposals = propose_from_recent_errors()
    if not proposals:
        proposals = [
            propose_improvement(
                "maintenance",
                "no_recent_error_signal",
                "Manter testes de compilacao e estado vivo antes de qualquer auto-melhoria.",
                "low",
            )
        ]
    experiment = create_experiment(
        "rsi_compile_baseline",
        "A Eve so deve integrar melhorias se o core compilar.",
        "py_compile_pass",
        "Correr py_compile nos modulos principais alterados.",
    )
    compile_result = run_python_compile(["main.py", "app/eve_codex.py"])
    rollback_plan = {
        "backup_dir": str(BACKUPS_DIR / "eve_versions"),
        "requires_tests_before_apply": True,
        "requires_human_or_policy_approval_for_core_write": True,
        "rollback_command": "git restore -- <changed-files> or restore from backups/eve_versions",
    }
    gates = {
        "sandbox_compile_passed": bool(compile_result.get("ok", False)),
        "core_write_blocked_in_cycle": True,
        "rollback_plan_present": True,
    }
    return {
        "proposals": [str(path) for path in proposals],
        "experiment": str(experiment),
        "compile": compile_result,
        "rollback_plan": rollback_plan,
        "gates": gates,
        "core_changed": False,
    }
