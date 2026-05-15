# Point 10 Errors And Terminal Runtime

Generated: 2026-05-15T16:56:04.978596Z
EVE_ROOT: `D:\Eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: valid PowerShell command succeeds
  - evidence: `{"timestamp": "2026-05-15T16:56:03.953779Z", "command": "Write-Output EveRuntimeTerminalOK", "cwd": "D:\\Eve", "allowed": true, "returncode": 0, "stdout": "EveRuntimeTerminalOK\n", "stderr": ""}`
- **PASS** critical: failing PowerShell command records failure
  - evidence: `{"timestamp": "2026-05-15T16:56:04.771148Z", "command": "Write-Error EveRuntimeTerminalFailure; exit 7", "cwd": "D:\\Eve", "allowed": true, "returncode": 7, "stdout": "", "stderr": "Write-Error EveRuntimeTerminalFailure; exit 7 : EveRuntimeTerminalFailure\n    + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException\n    + FullyQualifiedErrorId : Microsoft.PowerShell.Commands.WriteErrorException\n \n"}`
- **PASS** critical: terminal log directory exists
  - evidence: `"D:\\Eve\\logs\\terminal"`
- **PASS** critical: error memory exists
  - evidence: `"D:\\Eve\\memory\\errors\\error_memory.jsonl"`
- **PASS** critical: recent errors include terminal failure
  - evidence: `[{"timestamp": "2026-05-15T16:02:12.310724Z", "source": "unit", "task": "terminal failure", "error_type": "exit_9", "error_text": "unit terminal failure", "lesson": "unit lesson", "resolved": false}, {"timestamp": "2026-05-15T16:45:40.956673Z", "source": "unit_improvement", "task": "planner", "error_type": "UnitPlannerError", "error_text": "planner should create candidate", "lesson": "unit", "resolved": false}, {"timestamp": "2026-05-15T16:45:48.142049Z", "source": "unit", "task": "terminal failure", "error_type": "exit_9", "error_text": "unit terminal failure", "lesson": "unit lesson", "resolved": false}, {"timestamp": "2026-05-15T16:45:56.143295Z", "source": "terminal", "task": "Write-Error EveRuntimeTerminalFailure; exit 7", "error_type": "exit_7", "error_text": "Write-Error EveRuntimeTerminalFailure; exit 7 : EveRuntimeTerminalFailure\n    + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException\n    + FullyQualifiedErrorId : Microsoft.PowerShell.Commands.WriteErrorException\n \n", "lesson": "", "resolved": false}, {"timestamp": "2026-05-15T16:46:01.022550Z", "source": "runtime", "task": "autonomous improvement", "error_type": "runtime_gap", "error_text": ...(truncated)`
