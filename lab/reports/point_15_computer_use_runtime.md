# Point 15 Computer Use VNext Runtime

Generated: 2026-05-15T16:04:50.097792Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: Playwright module available for DOM route
  - evidence: `{"available": true, "engine": "playwright", "attached": false, "elements": []}`
- **PASS** critical: DOM snapshot reports Playwright engine before OCR
  - evidence: `{"available": true, "engine": "playwright", "attached": false, "elements": []}`
- **PASS** critical: click_by_role without page fails without using OCR
  - evidence: `{"ok": false, "engine": "playwright", "action": "click_by_role", "detail": {"reason": "no playwright page attached", "role": "button", "name": "Save"}}`
- **PASS**: fill_by_label without page fails without using OCR
  - evidence: `{"ok": false, "engine": "playwright", "action": "fill_by_label", "detail": {"reason": "no playwright page attached", "label": "Email"}}`
- **PASS** critical: UIA tree can be requested
  - evidence: `{"available": true, "engine": "uia", "active_window": "Windows PowerShell", "tree": {"element_id": "0:0:Console Window", "name": "Windows PowerShell", "control_type": "WindowControl", "automation_id": "Console Window", "enabled": true, "children": [{"element_id": "1:0:NonClientVerticalScrollBar", "name": "Vertical", "control_type": "ScrollBarControl", "automation_id": "NonClientVerticalScrollBar", "enabled": true, "children": [{"element_id": "2:0:UpButton", "name": "Linha para cima", "control_type": "ButtonControl", "automation_id": "UpButton", "enabled": true, "children": null}, {"element_id": "2:1:ScrollbarThumb", "name": "Posição", "control_type": "ThumbControl", "automation_id": "ScrollbarThumb", "enabled": true, "children": null}, {"element_id": "2:2:DownPageButton", "name": "Página para baixo", "control_type": "ButtonControl", "automation_id": "DownPageButton", "enabled": true, "children": null}, {"element_id": "2:3:DownButton", "name": "Linha para baixo", "control_type": "ButtonControl", "automation_id": "DownButton", "enabled": true, "children": null}]}, {"element_id": "1:1:TitleBarControl", "name": "", "control_type": "TitleBarControl", "automation_id": "", "enabled": true...(truncated)`
- **PASS** critical: UIA find_element works by name/control_type
  - evidence: `{"found": true, "element": {"name": "Save", "control_type": "Button", "element_id": "save"}, "engine": "uia"}`
- **PASS** critical: action router types via UIA before OCR
  - evidence: `{"ok": true, "engine": "uia", "attempts": [{"ok": true, "engine": "uia", "action": "type", "element": {"name": "Editor", "control_type": "Edit", "element_id": "edit"}, "text_length": 5, "simulated": true}], "verification": {"verified": false, "diff": {"changed": false, "changes": {}}, "reason": "no observable change"}, "permission": {"allowed": true, "policy": {"can_click": true, "can_type": true}}}`
- **PASS** critical: sensitive browser action blocks without confirmation
  - evidence: `{"ok": false, "stage": "permission", "permission": {"allowed": false, "reason": "sensitive action requires confirmation", "policy": {"can_click": true, "can_type": true, "requires_submit_confirmation": true}, "confirmation_required": true}}`
- **PASS**: OCR fallback is attempted only after structured route fails
  - evidence: `{"ok": false, "engine": null, "attempts": [{"ok": false, "engine": "uia", "action": "invoke", "reason": "element not found", "query": {"name": "definitely_missing_runtime_text", "control_type": null, "automation_id": null}}, {"ok": false, "engine": "ocr", "action": "click", "reason": "texto nao localizado por OCR"}], "verification": {"verified": false, "diff": {"changed": true, "changes": {"timestamp": {"before": "2026-05-15T16:04:49.131777Z", "after": "2026-05-15T16:04:50.071307Z"}}}, "missing": ["ocr_text"], "expected_change": {"ocr_text": "missing"}}, "permission": {"allowed": true, "policy": {"can_click": true, "can_type": true}}}`
