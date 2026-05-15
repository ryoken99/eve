# Point 10 Errors And Terminal Runtime

Generated: 2026-05-15T15:27:19.112867Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: valid PowerShell command succeeds
  - evidence: `{"timestamp": "2026-05-15T15:27:18.442189Z", "command": "Write-Output EveRuntimeTerminalOK", "cwd": "E:\\eve", "allowed": true, "returncode": 0, "stdout": "EveRuntimeTerminalOK\n", "stderr": ""}`
- **PASS** critical: failing PowerShell command records failure
  - evidence: `{"timestamp": "2026-05-15T15:27:18.858666Z", "command": "Write-Error EveRuntimeTerminalFailure; exit 7", "cwd": "E:\\eve", "allowed": true, "returncode": 7, "stdout": "", "stderr": "Write-Error EveRuntimeTerminalFailure; exit 7 : EveRuntimeTerminalFailure\n    + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException\n    + FullyQualifiedErrorId : Microsoft.PowerShell.Commands.WriteErrorException\n \n"}`
- **PASS** critical: terminal log directory exists
  - evidence: `"E:\\eve\\logs\\terminal"`
- **PASS** critical: error memory exists
  - evidence: `"E:\\eve\\memory\\errors\\error_memory.jsonl"`
- **PASS** critical: recent errors include terminal failure
  - evidence: `[{"timestamp": "2026-05-15T15:08:16.767482Z", "source": "terminal", "task": "Write-Error EveRuntimeTerminalFailure; exit 7", "error_type": "exit_7", "error_text": "Write-Error EveRuntimeTerminalFailure; exit 7 : EveRuntimeTerminalFailure\n    + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException\n    + FullyQualifiedErrorId : Microsoft.PowerShell.Commands.WriteErrorException\n \n", "lesson": "", "resolved": false}, {"timestamp": "2026-05-15T15:08:21.217026Z", "source": "runtime", "task": "autonomous improvement", "error_type": "runtime_gap", "error_text": "capability gap fake", "lesson": "turn gap into test", "resolved": false}, {"timestamp": "2026-05-15T15:20:32.729579Z", "source": "runtime", "task": "autonomous improvement", "error_type": "runtime_gap", "error_text": "capability gap fake", "lesson": "turn gap into test", "resolved": false}, {"timestamp": "2026-05-15T15:21:28.184369Z", "source": "terminal", "task": "Write-Error EveRuntimeTerminalFailure; exit 7", "error_type": "exit_7", "error_text": "Write-Error EveRuntimeTerminalFailure; exit 7 : EveRuntimeTerminalFailure\n    + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException...(truncated)`
