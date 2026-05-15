from __future__ import annotations

from runtime_validation_lib import check, finalize

from core.paths import LOGS_DIR, MEMORY_DIR
from memory.errors.error_memory import recent_errors
from tools.terminal import run_command


def main() -> dict:
    ok = run_command("Write-Output EveRuntimeTerminalOK", cwd=str(MEMORY_DIR.parent), approved=True)
    bad = run_command("Write-Error EveRuntimeTerminalFailure; exit 7", cwd=str(MEMORY_DIR.parent), approved=True)
    terminal_log = LOGS_DIR / "terminal"
    error_memory = MEMORY_DIR / "errors" / "error_memory.jsonl"
    errors = recent_errors(limit=10)
    checks = [
        check("valid PowerShell command succeeds", ok.get("returncode") == 0, ok, critical=True),
        check("failing PowerShell command records failure", bad.get("returncode") != 0, bad, critical=True),
        check("terminal log directory exists", terminal_log.exists(), str(terminal_log), critical=True),
        check("error memory exists", error_memory.exists(), str(error_memory), critical=True),
        check("recent errors include terminal failure", any("EveRuntimeTerminalFailure" in str(row) for row in errors), errors, critical=True),
    ]
    return finalize("point_10_errors_terminal_runtime", "Point 10 Errors And Terminal Runtime", "point_10_errors_terminal_runtime.md", checks)


if __name__ == "__main__":
    main()
