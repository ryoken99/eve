from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    checks = []
    test_command = (
        [sys.executable, "-m", "pytest", "tests/test_core.py", "tests/capabilities", "-q"]
        if importlib.util.find_spec("pytest")
        else [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py"]
    )
    for command in (test_command, [sys.executable, "scripts/run_capability_tests.py"]):
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        checks.append({"command": command, "returncode": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]})
    ok = all(row["returncode"] == 0 for row in checks)
    path = ROOT / "logs" / "capability_runs" / f"full_healthcheck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "ok": ok, "checks": checks}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": ok, "log": str(path)}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
