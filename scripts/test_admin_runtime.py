from __future__ import annotations

from runtime_validation_lib import check, finalize, run_step

from tools.admin_executor import admin_status, launch_elevated_powershell
from tools.windows_scheduler import create_daily_task, list_eve_tasks


def main() -> dict:
    status = admin_status()
    checks = [
        check("admin_status returns runtime data", "is_admin_process" in status and "audit_log" in status, status, critical=True),
        check("current process admin state detected", isinstance(status.get("is_admin_process"), bool), status.get("is_admin_process"), critical=True),
        run_step("elevated PowerShell can be prepared as dry-run", lambda: launch_elevated_powershell("Write-Host EveAdminRuntime", reason="runtime validation", dry_run=True), critical=True),
        run_step("Windows task with RunLevel Highest can be requested", lambda: create_daily_task("RuntimeValidationAdmin", "23:59", "cmd.exe /c echo EveRuntime", highest=True)),
        run_step("Eve scheduled tasks can be listed", list_eve_tasks),
    ]
    return finalize("point_01_admin_runtime", "Point 01 Admin Runtime", "point_01_admin_runtime.md", checks)


if __name__ == "__main__":
    main()
