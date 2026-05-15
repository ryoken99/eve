from __future__ import annotations

from pathlib import Path

from runtime_validation_lib import check, finalize

from core.paths import EVE_ROOT, WORKSPACE_DIR
from self_improvement.arsi_cycle import arsi_core_update


def main() -> dict:
    safe = arsi_core_update("workspace/arsi_test_module.py", "VALUE = 'valid'\n", tests=["py_compile_candidate"], approved=True)
    invalid_target = WORKSPACE_DIR / "arsi_invalid_module.py"
    invalid_target.write_text("VALUE = 'original'\n", encoding="utf-8")
    invalid = arsi_core_update("workspace/arsi_invalid_module.py", "def broken(:\n", tests=["py_compile_candidate"], approved=True)
    core_blocked = arsi_core_update("core/arsi_runtime_blocked.py", "VALUE = 1\n", tests=["py_compile_candidate"], approved=False)
    checks = [
        check("ARSI applies valid safe workspace update", safe.get("applied"), safe, critical=True),
        check("ARSI confirms py_compile for valid update", safe.get("tests_passed"), safe, critical=True),
        check("ARSI failing update does not apply", not invalid.get("applied") and invalid.get("status") == "failed_tests", invalid, critical=True),
        check("rollback or no-apply evidence is available", invalid.get("rollback_ready") or not invalid.get("applied"), invalid, critical=True),
        check("high-risk core change blocks without approval", core_blocked.get("status") == "blocked", core_blocked, critical=True),
    ]
    return finalize("point_16_arsi_runtime", "Point 16 ARSI Runtime", "point_16_arsi_runtime.md", checks)


if __name__ == "__main__":
    main()
