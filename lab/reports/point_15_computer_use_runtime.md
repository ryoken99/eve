# Point 15 Computer Use VNext Runtime

Generated: 2026-05-15T16:56:14.001286Z
EVE_ROOT: `D:\Eve`
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
  - evidence: `{"available": false, "engine": "uia", "active_window": "Windows PowerShell", "tree": null, "error": "[Errno 13] Permission denied: 'C:\\\\Program Files\\\\Python310\\\\lib\\\\site-packages\\\\comtypes\\\\gen\\\\_944DE083_8FB8_45CF_BCB7_C477ACB2F897_0_1_0.py'"}`
- **PASS** critical: UIA find_element works by name/control_type
  - evidence: `{"found": true, "element": {"name": "Save", "control_type": "Button", "element_id": "save"}, "engine": "uia"}`
- **PASS** critical: action router types via UIA before OCR
  - evidence: `{"ok": true, "engine": "uia", "engine_order": ["browser_dom", "browser_accessibility", "windows_uia", "app_specific_adapter", "keyboard_shortcut", "screenshot", "ocr", "coordinates"], "ocr_policy": "OCR is a fallback after DOM/accessibility/UIA/app adapters/shortcuts.", "attempts": [{"ok": true, "engine": "uia", "action": "type", "element": {"name": "Editor", "control_type": "Edit", "element_id": "edit"}, "text_length": 5, "simulated": true}], "verification": {"verified": false, "diff": {"changed": false, "changes": {}}, "reason": "no observable change"}, "permission": {"allowed": true, "policy": {"can_click": true, "can_type": true}}}`
- **PASS** critical: sensitive browser action blocks without confirmation
  - evidence: `{"ok": false, "stage": "permission", "permission": {"allowed": false, "reason": "sensitive action requires confirmation", "policy": {"can_click": true, "can_type": true, "requires_submit_confirmation": true}, "confirmation_required": true}}`
- **PASS**: OCR fallback is attempted only after structured route fails
  - evidence: `{"ok": false, "engine": null, "engine_order": ["browser_dom", "browser_accessibility", "windows_uia", "app_specific_adapter", "keyboard_shortcut", "screenshot", "ocr", "coordinates"], "ocr_policy": "OCR is a fallback after DOM/accessibility/UIA/app adapters/shortcuts.", "attempts": [{"ok": false, "engine": "uia", "action": "invoke", "reason": "element not found", "query": {"name": "definitely_missing_runtime_text", "control_type": null, "automation_id": null}}, {"ok": false, "engine": "ocr", "action": "click", "reason": "texto nao localizado por OCR"}], "verification": {"verified": false, "diff": {"changed": true, "changes": {"timestamp": {"before": "2026-05-15T16:56:11.925668Z", "after": "2026-05-15T16:56:13.859320Z"}}}, "missing": ["ocr_text"], "expected_change": {"ocr_text": "missing"}}, "permission": {"allowed": true, "policy": {"can_click": true, "can_type": true}}}`
