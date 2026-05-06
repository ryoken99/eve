from __future__ import annotations

from pathlib import Path

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
    return {
        "proposals": [str(path) for path in proposals],
        "experiment": str(experiment),
        "compile": compile_result,
        "core_changed": False,
    }
