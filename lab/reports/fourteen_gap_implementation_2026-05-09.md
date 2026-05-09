# Fourteen Gap Implementation - 2026-05-09

## Summary

Implemented functional MVPs for the 14 Hermes/OpenClaw-inspired gaps identified for Eve. These are not full parity with Hermes/OpenClaw, but each gap now has a concrete module, callable functions, and formal LLM tools where appropriate.

## Implemented

1. Plugin discovery: `core/plugin_registry.py`
2. Tool policy classifier: `security/tool_policy.py`
3. Session database/search/export: `core/session_store.py`
4. Local cron manager: `autonomy/cron_manager.py`
5. Background process manager: `tools/process_manager.py`
6. Subagent manager: `core/subagent_manager.py`
7. Vector memory provider: `memory/vector_provider.py`
8. Skill curator: `learning/skill_curator.py`
9. Gateway/mobile foundation remains via existing `tools/mobile_bridge.py`; registry now has supporting diagnostics/process/session tools for future gateway hardening.
10. Browser advanced tools: `tools/browser_advanced.py`
11. Secrets vault/masking: `security/secrets_vault.py`
12. Diagnostics export: `core/diagnostics.py`
13. Startup daemon installers: `autonomy/startup_service.py`
14. Trigger engine: `autonomy/trigger_engine.py`

## Registry

`core/eve_tool_registry.py` now exposes 81 formal LLM tools.

## Verification

- `python -m py_compile ...` passed for new modules.
- `python -m unittest tests.test_core` passed: 60 tests.

## Remaining Hardening

- Plugin SDK should support tool registration, not only manifest discovery.
- Tool policy should be enforced before execution for all sensitive classes, not only reported.
- Session store should ingest normal chat logs automatically.
- Cron manager should support richer schedules and missed-run recovery.
- Process manager should persist return codes and stream tails.
- Subagents need structured result handoff, cancellation and bounded concurrency.
- Vector provider should move from TF-IDF/local token vectors to embeddings/Chroma.
- Skill curator needs backup/restore UI and automatic usage integration in `run_skill`.
- Mobile/gateway layer still needs a real always-available HTTP/chat interface.
- Browser tools need CDP/Playwright or stronger OCR action verification.
- Secrets vault should use Windows DPAPI or credential manager for real encryption.
- Diagnostics should include trajectory timeline and redaction.
- Startup daemon should be installed as a robust startup/background service.
- Trigger engine should be connected to the daemon and Token Gate.

