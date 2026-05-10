# Session Handoff and Internal Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Eve rotate sessions before model context is exhausted while preserving the thread, and let Eve use internal commands/tools herself instead of asking Sandro to type them.

**Architecture:** Add a deterministic handoff layer that stores active session id, recent-message summaries, active missions, and resume notes. Add an internal command planner that maps natural requests to available Eve tools and injects those suggestions into the model prompt.

**Tech Stack:** Python standard library, existing Eve session store, mission control, tool registry, unittest.

---

### Task 1: Session Store Accessors

**Files:**
- Modify: `core/session_store.py`
- Test: `tests/test_core.py`

- [x] Add `count_session_messages(session_id)`.
- [x] Add `recent_session_messages(session_id, limit)`.
- [x] Verify they return ordered, JSON-decoded records.

### Task 2: Session Handoff Manager

**Files:**
- Create: `core/session_handoff.py`
- Test: `tests/test_core.py`

- [x] Add active session state in `state/current_session.json`.
- [x] Add `create_session_checkpoint()`.
- [x] Add `load_active_handoff()`.
- [x] Add `rotate_session()`.
- [x] Add `context_status()`.

### Task 3: Internal Command Planner

**Files:**
- Create: `core/internal_command_planner.py`
- Test: `tests/test_core.py`

- [x] Map natural intents like loop, mission, browser, terminal, memory, daemon, vector, X posts and research to tools.
- [x] Return concise suggestions for prompt injection.
- [x] Avoid executing anything directly; planner advises the LLM/tool loop.

### Task 4: Tool Registry Integration

**Files:**
- Modify: `core/eve_tool_registry.py`
- Modify: `security/tool_policy.py`
- Test: `tests/test_core.py`

- [x] Expose `session_checkpoint`, `session_resume`, `session_rotate`, `context_status`, and `internal_plan`.
- [x] Classify read-only vs mutating session tools.
- [x] Update catalog rules so Eve uses tools instead of asking Sandro to type commands.

### Task 5: Chat Prompt Integration

**Files:**
- Modify: `app/eve_codex.py`
- Test: `python -m unittest tests.test_core`

- [x] Replace fixed `SESSION_ID` with active session id.
- [x] Inject active handoff/resume context.
- [x] Inject internal command planner suggestions.
- [x] Auto checkpoint when context status crosses warning threshold.

### Verification

- [x] `python -m compileall app core security tests`
- [x] `python -m unittest tests.test_core`
