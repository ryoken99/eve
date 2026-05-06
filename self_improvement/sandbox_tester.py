from __future__ import annotations

import subprocess
import sys

from security.audit_log import log_event


def run_python_compile(paths: list[str]) -> dict:
    command = [sys.executable, "-m", "py_compile", *paths]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    result = {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }
    log_event("sandbox_compile_test", result)
    return result
