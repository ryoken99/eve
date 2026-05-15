# Sprint 0 Runtime Environment

Generated: 2026-05-15T16:55:44.115611Z
EVE_ROOT: `D:\Eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: Python is available
  - evidence: `{"executable": "C:\\Program Files\\Python310\\python.exe", "version": "3.10.11 (tags/v3.10.11:7d4cc5a, Apr  5 2023, 00:38:17) [MSC v.1929 64 bit (AMD64)]"}`
- **PASS**: venv python exists
  - evidence: `"D:\\Eve\\.venv\\Scripts\\python.exe"`
- **PASS** critical: Playwright Python module importable
  - evidence: `{"name": "playwright", "available": true, "version": null}`
- **PASS**: pyautogui importable
  - evidence: `{"name": "pyautogui", "available": true, "version": "0.9.54"}`
- **PASS** critical: uiautomation importable
  - evidence: `{"name": "uiautomation", "available": true, "version": null}`
- **PASS**: PIL importable
  - evidence: `{"name": "PIL", "available": true, "version": "11.2.1"}`
- **PASS**: pytesseract importable if installed
  - evidence: `{"name": "pytesseract", "available": true, "version": "0.3.13"}`
- **PASS** critical: EVE_ROOT exists and is writable
  - evidence: `"D:\\Eve"`
- **PASS** critical: PC path detected
  - evidence: `{"pc": "PC1", "root": "D:\\Eve", "drive": "D:", "expected_pc1": "D:\\Eve", "expected_pc2": "E:\\eve"}`
- **PASS** critical: config.yaml exists
  - evidence: `"D:\\Eve\\config.yaml"`
- **PASS**: default mode remains unrestricted_mode
  - evidence: `{"mode": "unrestricted_mode"}`

## Summary

```json
{
  "imports": {
    "python": "3.10.11 (tags/v3.10.11:7d4cc5a, Apr  5 2023, 00:38:17) [MSC v.1929 64 bit (AMD64)]",
    "platform": "Windows-10-10.0.26200-SP0",
    "modules": {
      "playwright": {
        "name": "playwright",
        "available": true,
        "version": null
      },
      "pyautogui": {
        "name": "pyautogui",
        "available": true,
        "version": "0.9.54"
      },
      "uiautomation": {
        "name": "uiautomation",
        "available": true,
        "version": null
      },
      "PIL": {
        "name": "PIL",
        "available": true,
        "version": "11.2.1"
      },
      "pytesseract": {
        "name": "pytesseract",
        "available": true,
        "version": "0.3.13"
      }
    }
  },
  "pc": {
    "pc": "PC1",
    "root": "D:\\Eve",
    "drive": "D:",
    "expected_pc1": "D:\\Eve",
    "expected_pc2": "E:\\eve"
  }
}
```
