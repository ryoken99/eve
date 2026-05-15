# Sprint 0 Runtime Environment

Generated: 2026-05-15T16:24:15.937214Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: Python is available
  - evidence: `{"executable": "C:\\Users\\Sandro\\AppData\\Local\\Programs\\Python\\Python311\\python.exe", "version": "3.11.7 (tags/v3.11.7:fa7a6f2, Dec  4 2023, 19:24:49) [MSC v.1937 64 bit (AMD64)]"}`
- **PASS**: venv python exists
  - evidence: `"E:\\eve\\.venv\\Scripts\\python.exe"`
- **PASS** critical: Playwright Python module importable
  - evidence: `{"name": "playwright", "available": true, "version": null}`
- **PASS**: pyautogui importable
  - evidence: `{"name": "pyautogui", "available": true, "version": "0.9.54"}`
- **PASS** critical: uiautomation importable
  - evidence: `{"name": "uiautomation", "available": true, "version": null}`
- **PASS**: PIL importable
  - evidence: `{"name": "PIL", "available": true, "version": "12.2.0"}`
- **PASS**: pytesseract importable if installed
  - evidence: `{"name": "pytesseract", "available": true, "version": "0.3.13"}`
- **PASS** critical: EVE_ROOT exists and is writable
  - evidence: `"E:\\eve"`
- **PASS** critical: PC path detected
  - evidence: `{"pc": "PC2", "root": "E:\\eve", "drive": "E:", "expected_pc1": "D:\\Eve", "expected_pc2": "E:\\eve"}`
- **PASS** critical: config.yaml exists
  - evidence: `"E:\\eve\\config.yaml"`
- **PASS**: default mode remains unrestricted_mode
  - evidence: `{"mode": "unrestricted_mode"}`

## Summary

```json
{
  "imports": {
    "python": "3.11.7 (tags/v3.11.7:fa7a6f2, Dec  4 2023, 19:24:49) [MSC v.1937 64 bit (AMD64)]",
    "platform": "Windows-10-10.0.19045-SP0",
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
        "version": "12.2.0"
      },
      "pytesseract": {
        "name": "pytesseract",
        "available": true,
        "version": "0.3.13"
      }
    }
  },
  "pc": {
    "pc": "PC2",
    "root": "E:\\eve",
    "drive": "E:",
    "expected_pc1": "D:\\Eve",
    "expected_pc2": "E:\\eve"
  }
}
```
