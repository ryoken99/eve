# Point 01 Admin Core

Goal: Eve must know when admin is needed, what kind of admin is needed and what admin state is currently available.

Implemented core:

- `core/admin_capability.py`
- `AdminState`
- `AdminIntent`
- `classify_admin_intent(command_or_task)`
- `admin_capability_status()`
- awareness integration in `core/awareness_engine.py`

8.6 criterion: met at core-contract level. Codex 2 must validate real elevated PowerShell/admin execution.
