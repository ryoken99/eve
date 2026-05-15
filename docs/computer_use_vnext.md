# Computer Use VNext

Eve's computer-use stack must prefer structured interfaces over pixels.

## Engine Priority

1. Browser DOM / Playwright
2. Browser accessibility tree / ARIA
3. Windows UI Automation
4. App-specific adapter
5. Keyboard shortcut
6. Screenshot
7. OCR
8. Coordinates

## Policy

OCR is a fallback, not Eve's primary vision system. Screenshots remain useful for verification and context, but action planning should first use DOM, accessibility and UIA whenever available.

## Runtime Expectations For Codex 2

- Use one browser tab when researching multi-source tasks where possible.
- Close pages after browser tasks unless Sandro asks to keep them open.
- Verify every browser action before reporting success.
- Record browser actions as structured transcript events.
