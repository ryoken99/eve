# Eve Full Project Review - 2026-05-08

## Scope

Review requested by Sandro: inspect the project folder-by-folder, compare it with the intended Eve plan, activate Codex-Eve loop mode 3, and correct blocking gaps found during the review.

## Confirmed Changes In This Review

- Loop mode is now `3` in `config/eve.json`, meaning Codex-Eve loop has no configured message limit when explicitly started.
- Added a local X scheduling bridge:
  - `tools/x_scheduler.py`
  - `scripts/run_x_post_job.py`
  - `/x-agendar HH:MM | text`
  - `python -m app.eve_codex x-schedule HH:MM "text"`
- Natural-language requests from Sandro to schedule an X post now route to the local scheduler before falling back to the LLM.
- CLI `ask` now also checks natural tool requests before calling the LLM, so this bridge is not limited to interactive chat mode.
- Added operational memory so Eve knows X scheduling is a real local capability.

## Folder Review

| Area | Folder | Status | Notes |
| --- | --- | --- | --- |
| Terminal interface | `app/` | Functional | Chat, menu, Codex auth, model selection, loop, many commands. `app/eve_codex.py` is large and should later be split. |
| Core state | `core/` | Functional | Awareness, mission control, personality scoring, self-report. |
| LLM/auth | `app/eve_codex.py`, `secrets/` | Functional locally | OAuth/device flow and multi-account support exist. Secrets are gitignored. |
| Memory | `memory/` | Functional, partial depth | Short/medium/long memory, diary, semantic TF-IDF, entity learning. True embedding database is still not implemented. |
| Diary/logs | `memory/diary`, `logs/` | Functional | Chat, audit, browser, UI, autonomy and loop logs exist. Runtime logs are gitignored. |
| Skills | `skills/`, `learning/` | Functional | Draft/trusted skills, X publishing, research, demonstration recorder, adaptive lessons. Skill self-versioning is still basic. |
| Browser/PC control | `tools/`, `computer/` | Functional but not mature | Chrome profile, screenshots, OCR hooks, mouse/keyboard, visual executor. Complex sites/apps still need supervised hardening. |
| X posting | `skills/trusted/x_publish_text_learning.json`, `tools/x_human.py` | Functional for tested cases | Can publish through visual skill with audit. Final feed verification still has OCR limitations. |
| X scheduling | `tools/x_scheduler.py`, `scripts/run_x_post_job.py` | Newly functional | Creates Windows scheduled task and job file for later execution. |
| Autonomy | `autonomy/`, `scripts/` | Functional MVP | Director, daemon tick, autonomous low-risk execution, Token Gate, reports. Not yet a 24/7 robust service with all triggers. |
| Research | `research/`, `tools/web_research.py` | Functional MVP | Structured reports with source facts and interpretation. Full human browser research remains partial. |
| Dream | `dream/` | Functional MVP | Creates reports and lab queue, but not yet scheduled multi-cycle dreaming. |
| Lab/self-improvement | `lab/`, `self_improvement/` | Functional MVP | Experiments, proposals, sandbox compile, controlled RSI. Core self-rewrite remains approval/test based. |
| Security/admin | `security/`, `tools/admin_executor.py` | Functional | Safety modes, permission checks, emergency lock, admin helper. Full unrestricted admin autonomy is intentionally gated. |
| Mobile/voice | `mobile_bridge/`, `tools/voice.py` | Basic | Local voice and mobile queue/server exist, but not mature assistant UX. |
| Tests | `tests/` | Functional | 38 unit tests currently cover core behavior. More integration tests are needed for live browser/UI. |

## Comparison With Original 25-Phase Plan

| Phase Group | Current Result |
| --- | --- |
| 0-2: foundation, chat, diary | Implemented. |
| 3-6: layered memory, consolidation, semantic memory, dreams | Implemented as MVP; vector memory is TF-IDF/local, not Chroma/embedding-grade. |
| 7-9: permissions, filesystem/terminal, error memory | Implemented as MVP. |
| 10,16,17: skills, demonstration learning, adaptive learning | Implemented as MVP; robust visual skill learning still needs more real-world training. |
| 11-13: awareness, screen, mouse/keyboard | Implemented as MVP. |
| 14-15: browser and email as human | Browser works for URL/search/X tested paths; Gmail draft exists; broad app/web reliability still partial. |
| 18-20: autonomy, research, personality | Implemented as MVP; persistent always-on runtime still needs stronger scheduler/service and trigger policy. |
| 21-25: lab, self-improvement, admin, any app, RSI | Implemented as controlled scaffold; not yet mature full recursive self-improvement. |

## Main Blocking Gap Found

Eve knew about the X publishing skill but did not have an operational bridge from natural-language scheduling requests to local execution. That caused her to answer "I cannot execute this from here" instead of scheduling the task.

## Fix Applied

The new bridge makes this flow real:

```text
Sandro natural request
  -> parse time + X intent
  -> draft English post
  -> write state/x_posts/job.json
  -> create Windows scheduled task
  -> scheduled runner calls trusted/x_publish_text_learning
  -> logs/audit result
```

## Remaining High-Value Work

1. Split `app/eve_codex.py` into command modules; it is doing too much.
2. Add real integration tests for `schtasks`, browser launch on monitor 3, and X composer verification.
3. Replace final X OCR check with timeline/profile URL verification where possible.
4. Make autonomy daemon install/start-on-login robust and visible in dashboard.
5. Add true embedding-based vector memory.
6. Add scheduled dream/consolidation/research tasks with clear cadence and reports.
7. Harden visual browser/app actions into reusable skills with screenshots before/after and selectors by text/image.
8. Add a capability self-test command that Eve can run before claiming she can do something.
