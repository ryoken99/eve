# Point 07 Awareness Runtime

Generated: 2026-05-15T15:27:17.529427Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: timezone captured
  - evidence: `"Europe/Lisbon"`
- **PASS** critical: active window captured
  - evidence: `{"active_window": "Windows PowerShell", "top_processes": ["Codex", "codex", "Codex", "nvcontainer", "chrome", "chrome", "Codex", "chrome", "explorer", "chrome", "rustdesk", "RuntimeBroker"]}`
- **PASS** critical: system status captured
  - evidence: `{"os": "Windows", "release": "10", "version": "10.0.19045", "machine": "AMD64"}`
- **PASS** critical: environment state captures UIA/browser fields
  - evidence: `{"timestamp": "2026-05-15T15:27:13.232977Z", "active_window": "Windows PowerShell", "browser": {"available": true, "engine": "playwright", "attached": false, "elements": []}, "uia": {"available": true, "engine": "uia", "active_window": "Windows PowerShell", "tree": {"element_id": "0:0:Console Window", "name": "Windows PowerShell", "control_type": "WindowControl", "automation_id": "Console Window", "enabled": true, "children": [{"element_id": "1:0:NonClientVerticalScrollBar", "name": "Vertical", "control_type": "ScrollBarControl", "automation_id": "NonClientVerticalScrollBar", "enabled": true, "children": [{"element_id": "2:0:UpButton", "name": "Linha para cima", "control_type": "ButtonControl", "automation_id": "UpButton", "enabled": true, "children": null}, {"element_id": "2:1:ScrollbarThumb", "name": "Posição", "control_type": "ThumbControl", "automation_id": "ScrollbarThumb", "enabled": true, "children": null}, {"element_id": "2:2:DownPageButton", "name": "Página para baixo", "control_type": "ButtonControl", "automation_id": "DownPageButton", "enabled": true, "children": null}, {"element_id": "2:3:DownButton", "name": "Linha para baixo", "control_type": "ButtonControl", "automat...(truncated)`
- **PASS**: Chrome launch command executed
  - evidence: `{"returncode": 0, "stdout": "", "stderr": ""}`
- **PASS**: PowerShell launch command executed
  - evidence: `{"returncode": 0, "stdout": "", "stderr": ""}`
- **PASS** critical: current_world_state.json written
  - evidence: `"E:\\eve\\state\\current_world_state.json"`
- **PASS**: post-launch awareness has active window string
  - evidence: `{"chrome": "about:blank - Google Chrome", "ps": "Windows PowerShell"}`
