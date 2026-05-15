# Point 10 Errors And Terminal Runtime

Generated: 2026-05-15T16:04:41.365683Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: valid PowerShell command succeeds
  - evidence: `{"timestamp": "2026-05-15T16:04:40.693621Z", "command": "Write-Output EveRuntimeTerminalOK", "cwd": "E:\\eve", "allowed": true, "returncode": 0, "stdout": "EveRuntimeTerminalOK\n", "stderr": ""}`
- **PASS** critical: failing PowerShell command records failure
  - evidence: `{"timestamp": "2026-05-15T16:04:41.105392Z", "command": "Write-Error EveRuntimeTerminalFailure; exit 7", "cwd": "E:\\eve", "allowed": true, "returncode": 7, "stdout": "", "stderr": "Write-Error EveRuntimeTerminalFailure; exit 7 : EveRuntimeTerminalFailure\n    + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException\n    + FullyQualifiedErrorId : Microsoft.PowerShell.Commands.WriteErrorException\n \n"}`
- **PASS** critical: terminal log directory exists
  - evidence: `"E:\\eve\\logs\\terminal"`
- **PASS** critical: error memory exists
  - evidence: `"E:\\eve\\memory\\errors\\error_memory.jsonl"`
- **PASS** critical: recent errors include terminal failure
  - evidence: `[{"timestamp": "2026-05-15T15:21:33.216503Z", "source": "runtime", "task": "autonomous improvement", "error_type": "runtime_gap", "error_text": "capability gap fake", "lesson": "turn gap into test", "resolved": false}, {"timestamp": "2026-05-15T15:23:07.476829Z", "source": "terminal", "task": "Write-Error EveRuntimeTerminalFailure; exit 7", "error_type": "exit_7", "error_text": "Write-Error EveRuntimeTerminalFailure; exit 7 : EveRuntimeTerminalFailure\n    + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException\n    + FullyQualifiedErrorId : Microsoft.PowerShell.Commands.WriteErrorException\n \n", "lesson": "", "resolved": false}, {"timestamp": "2026-05-15T15:23:12.632020Z", "source": "runtime", "task": "autonomous improvement", "error_type": "runtime_gap", "error_text": "capability gap fake", "lesson": "turn gap into test", "resolved": false}, {"timestamp": "2026-05-15T15:25:31.012433Z", "source": "unit_improvement", "task": "planner", "error_type": "UnitPlannerError", "error_text": "planner should create candidate", "lesson": "unit", "resolved": false}, {"timestamp": "2026-05-15T15:25:43.491176Z", "source": "unit", "task": "terminal failure", "error_type": ...(truncated)`
