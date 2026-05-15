# Point 07 Awareness Runtime

Generated: 2026-05-15T16:04:39.790424Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: timezone captured
  - evidence: `"Europe/Lisbon"`
- **PASS** critical: active window captured
  - evidence: `{"active_window": "Codex", "top_processes": ["Codex", "codex", "Codex", "nvcontainer", "Codex", "chrome", "chrome", "chrome", "rustdesk", "explorer", "AdobeCollabSync", "chrome"]}`
- **PASS** critical: system status captured
  - evidence: `{"os": "Windows", "release": "10", "version": "10.0.19045", "machine": "AMD64"}`
- **PASS** critical: environment state captures UIA/browser fields
  - evidence: `{"timestamp": "2026-05-15T16:04:35.486123Z", "active_window": "Codex", "browser": {"available": true, "engine": "playwright", "attached": false, "elements": []}, "uia": {"available": true, "engine": "uia", "active_window": "Codex", "tree": {"element_id": "0:0:Codex", "name": "Codex", "control_type": "WindowControl", "automation_id": "", "enabled": true, "children": [{"element_id": "1:0:PaneControl", "name": "", "control_type": "PaneControl", "automation_id": "", "enabled": true, "children": []}, {"element_id": "1:1:Codex", "name": "Codex", "control_type": "PaneControl", "automation_id": "", "enabled": true, "children": [{"element_id": "2:0:PaneControl", "name": "", "control_type": "PaneControl", "automation_id": "", "enabled": true, "children": null}]}]}}}`
- **PASS**: Chrome launch command executed
  - evidence: `{"returncode": 0, "stdout": "", "stderr": ""}`
- **PASS**: PowerShell launch command executed
  - evidence: `{"returncode": 0, "stdout": "", "stderr": ""}`
- **PASS** critical: current_world_state.json written
  - evidence: `"E:\\eve\\state\\current_world_state.json"`
- **PASS**: post-launch awareness has active window string
  - evidence: `{"chrome": "about:blank - Google Chrome", "ps": "Windows PowerShell"}`
