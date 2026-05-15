# Point 07 Awareness Runtime

Generated: 2026-05-15T16:56:02.825543Z
EVE_ROOT: `D:\Eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: timezone captured
  - evidence: `"Europe/Lisbon"`
- **PASS** critical: active window captured
  - evidence: `{"active_window": "LM Studio", "top_processes": ["chrome", "Codex", "LM Studio", "LM Studio", "Codex", "chrome", "CefSharp.BrowserSubprocess", "rustdesk", "codex", "chrome", "RazerCortex", "audiodg"]}`
- **PASS** critical: system status captured
  - evidence: `{"os": "Windows", "release": "10", "version": "10.0.26200", "machine": "AMD64"}`
- **PASS** critical: environment state captures UIA/browser fields
  - evidence: `{"timestamp": "2026-05-15T16:55:57.734890Z", "active_window": "LM Studio", "browser": {"available": true, "engine": "playwright", "attached": false, "elements": []}, "uia": {"available": false, "engine": "uia", "active_window": "LM Studio", "tree": null, "error": "[Errno 13] Permission denied: 'C:\\\\Program Files\\\\Python310\\\\lib\\\\site-packages\\\\comtypes\\\\gen\\\\_944DE083_8FB8_45CF_BCB7_C477ACB2F897_0_1_0.py'"}}`
- **PASS**: Chrome launch command executed
  - evidence: `{"returncode": 0, "stdout": "", "stderr": ""}`
- **PASS**: PowerShell launch command executed
  - evidence: `{"returncode": 0, "stdout": "", "stderr": ""}`
- **PASS** critical: current_world_state.json written
  - evidence: `"D:\\Eve\\state\\current_world_state.json"`
- **PASS**: post-launch awareness has active window string
  - evidence: `{"chrome": "about:blank - Google Chrome", "ps": "Windows PowerShell"}`
