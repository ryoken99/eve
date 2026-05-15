# Integration Rules

## Branch Order

1. Codex 1 works on `pc1/eve-17-points-core-upgrade`.
2. Codex 1 opens PR to `main`.
3. Codex 2 merges/rebases from `main`.
4. Codex 2 works on `pc2/eve-17-points-runtime-validation`.
5. Codex 2 opens PR to `main`.

## Shared Rules

- Do not remove an existing module unless a better replacement is committed.
- Do not commit private runtime memory/state unless Sandro explicitly asks.
- Keep `unrestricted_mode` as the project default.
- Runtime should report tool/action results as structured transcript events.
- Browser research should use one working tab where possible and close pages when done.
- Post/task success requires verification, not just intent.
- Multi-step user requests require a checklist and final verification count.

## Point 15 Priority

Computer-use engines must be attempted in this order:

1. DOM / Playwright
2. Browser accessibility tree / ARIA
3. Windows UI Automation
4. App-specific adapter
5. Keyboard shortcut
6. Screenshot
7. OCR
8. Coordinates
