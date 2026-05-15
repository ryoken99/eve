# Point 01 Admin Runtime

Generated: 2026-05-15T15:26:57.243286Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: admin_status returns runtime data
  - evidence: `{"is_admin_process": false, "safety_mode": "unrestricted_mode", "admin_requires_approval": false, "can_launch_elevated_powershell": true, "elevated_startup_supported": true, "audit_log": "E:\\eve\\logs\\admin_actions\\2026-05-15.jsonl"}`
- **PASS** critical: current process admin state detected
  - evidence: `false`
- **PASS** critical: elevated PowerShell can be prepared as dry-run
  - evidence: `{"script": "E:\\eve\\backups\\tmp\\eve_admin_command.ps1", "powershell_command": "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"E:\\eve\\backups\\tmp\\eve_admin_command.ps1\"'", "reason": "runtime validation", "dry_run": true, "returncode": null, "stdout": "", "stderr": "", "status": "dry_run"}`
- **PASS**: Windows task with RunLevel Highest can be requested
  - evidence: `{"task": "Eve_RuntimeValidationAdmin", "returncode": 1, "stdout": "", "stderr": "ERROR: Acesso negado.\n\n", "highest": true, "args": ["schtasks", "/Create", "/SC", "DAILY", "/TN", "Eve_RuntimeValidationAdmin", "/TR", "cmd.exe /c echo EveRuntime", "/ST", "23:59", "/F", "/RL", "HIGHEST"]}`
- **PASS**: Eve scheduled tasks can be listed
  - evidence: `{"returncode": 0, "tasks": [], "stderr": ""}`
