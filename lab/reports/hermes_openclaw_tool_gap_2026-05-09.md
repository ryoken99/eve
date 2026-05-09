# Hermes/OpenClaw Tool Gap Review - 2026-05-09

## Sources Checked

- Hermes Agent local clone: `external/hermes-agent`, commit `f6d45e5`.
- OpenClaw local clone: `external/openclaw`, commit `a99729fd`.
- Eve local registry: `core/eve_tool_registry.py`, 47 formal LLM tools.
- Eve project reports: `lab/reports/eve_full_project_review_2026-05-08.md`, `lab/reports/requirements_gap_2026-05-06.md`.
- Sandro's extracted requirements: `memory/sandro_original_eve_requests.md`, `docs/eve_requirements_consciousness_and_dreams_2026-05-07.md`.

## Current Eve Tool Coverage

Eve now exposes formal LLM tools for:

- capability self-test;
- desktop file/folder creation;
- browser open/search;
- web research reports;
- X scheduling and X publishing;
- terminal command execution;
- trusted skill execution;
- workspace file list/read/write/append;
- screen screenshots/OCR/monitor reports;
- mouse and keyboard control;
- Gmail draft/search;
- Windows notifications;
- awareness;
- diary and memory read/write/append/context;
- autonomy cycle;
- Windows scheduled tasks;
- safety mode and admin helpers.

## Hermes Capabilities Not Yet Mature In Eve

Hermes has several mature surfaces that Eve only partially has:

- Tool auto-discovery by module registration and toolsets.
- Enable/disable toolsets per platform/profile.
- Plugin lifecycle hooks: `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, session hooks.
- Memory-provider plugin abstraction with `sync_turn`, `prefetch`, and swappable providers.
- Session database with searchable conversation history.
- Skill curator that tracks skill usage, staleness, archive/restore and backups.
- Cron system with pause/resume/edit/trigger/list and schedule formats beyond simple Windows tasks.
- Delegation/subagents with isolated contexts and bounded concurrency.
- Rich TUI/dashboard with tool progress and approval prompts.
- Process management/background terminal jobs.
- Code execution tool for multi-step tool calls without many LLM round trips.
- Clarifying-question tool.
- TTS/voice as a real tool.
- Home Assistant, Discord, Slack, Telegram, SMS and other messaging platforms.
- Image/video generation and analysis tools.
- Observability/metrics/traces plugins.

## OpenClaw Capabilities Not Yet Mature In Eve

OpenClaw has stronger infrastructure in these areas:

- Gateway with channels, identity/pairing, command authorization and owner scopes.
- Native slash command system, directives, session controls and model/run controls.
- Tool policy / approval classification by tool type: readonly, search, exec, control-plane, mutating.
- Sandbox vs host vs elevated execution separation.
- ACP/subagent/session management.
- Tool inventory and effective tool policy tests.
- Config/schema system with provider/tool/plugin settings.
- SecretRef/secrets handling and credential semantics.
- Web search providers with fallback, caching, provider selection and SSRF protection.
- `web_fetch`, `x_search`, PDF/media/image/music/video tools.
- Background processes, job polling, stop/poll commands.
- Trajectory/session export for debugging and replay.
- Plugin SDK and plugin commands.
- Command queue/steering/interrupt handling.
- Compaction/runtime context/prompt drift tests.
- Gateway health/readiness/diagnostics/observability.
- Remote gateway/Tailscale/Bonjour discovery.
- Voice/realtime talk pipeline.

## High-Priority Features To Bring Into Eve

1. Dynamic tool/plugin registry with auto-discovery instead of editing `core/eve_tool_registry.py` for every tool.
2. Tool policy classifier with approval classes: readonly, mutating, exec, public, admin, self-modify.
3. Real session store with searchable transcripts and trajectory export.
4. Better scheduler/cron abstraction: list, pause, resume, edit, run-now, missed-run recovery.
5. Background process manager for long terminal/browser/research tasks.
6. Subagent/delegation system for parallel research/coding/review tasks.
7. Memory provider interface with sync/prefetch, plus true vector embeddings.
8. Skill curator: usage tracking, stale detection, archive/restore, backups.
9. Gateway/mobile/chat channel layer so Eve can speak from phone/browser/API reliably.
10. Tool result UI/progress feed so Sandro sees exactly what Eve is doing.
11. Robust browser automation split: browser open/search is not enough; needs snapshot, click, type, scroll, console/CDP or OCR alternatives.
12. Secrets/credential vault with explicit no-log masking.
13. Config schema and doctor/diagnostics command.
14. Compaction and runtime context tests so Eve keeps identity/memory/tools after long chats.

## Sandro Requirement Status

### Achieved As Functional MVP

- Local Eve project at `D:\Eve`.
- Codex/OpenAI OAuth login and multi-account support.
- Terminal chat and model selection.
- Diary/chat logging.
- Short/medium/long memory files.
- Sandro base memory imported from entity files.
- Eve identity/personality files, Helix influence and soul/persona.
- Tools exposed to LLM via formal registry.
- Browser open/search with Chrome Eve profile.
- X posting skill and X scheduling.
- Desktop file/folder creation and scheduled folder task.
- Terminal execution with logs.
- Workspace file read/write.
- Awareness of time/system/window/processes.
- Screenshots, monitor detection and OCR hooks.
- Mouse and keyboard control.
- Gmail draft/search foundations.
- Error logs and adaptive lesson records.
- Skills in draft/trusted form and skill runner.
- Demonstration and adaptive learning scaffold.
- Autonomy director, token gate and low-risk autonomy cycle.
- Lab/reports/candidate improvements.
- Sandbox compile testing.
- Safety modes including `unrestricted_mode`.
- Admin helper/elevated PowerShell launcher.
- Codex-instructor vs Sandro speaker separation.
- Codex-Eve loop mode 1/2/3.
- GitHub repo and pushes.

### Partial / Needs Hardening

- Memory vector/semantic system exists only as lightweight/local index, not Chroma/embedding-grade.
- Dreams and consolidation exist but are not yet robust scheduled multi-cycle background habits.
- Proactivity exists as low-risk cycle, not full always-awake daemon/service.
- Browser can open/search and some X flows work, but broad human-level browsing needs more visual/action verification.
- Email can create drafts, but full Gmail workflow with attachments/reply/send guard is not mature.
- Learn-by-demonstration exists in format, not full automatic recording/interpreting of real mouse/keyboard demos.
- Adaptive learning records corrections, but automatic skill patch/test/promote loop is still basic.
- Admin mode exists, but real elevated execution still depends on UAC/process state.
- Self-improvement scaffold exists, but full patch/test/rollback/apply pipeline is not mature.
- Personality and preferences exist in files, but decision influence is still limited.
- Research reports exist, but daily autonomous research watcher is not yet robust.

### Still Missing Or Not Mature Enough

- Persistent Windows service/startup daemon that keeps Eve awake 24/7 without wasting LLM tokens.
- Robust trigger engine that creates missions from errors, memory drift, world news, PC activity and Eve curiosity.
- Real plugin SDK for Eve tools/skills.
- Swappable memory providers and true embeddings.
- Subagents/delegated workers.
- Full session database and search over all conversations/tool traces.
- Tool approval classifier and per-tool risk policy stronger than current safety mode.
- Better visual browser toolset: snapshot, click, type, scroll, back, console, dialog handling, page extraction.
- Background terminal/process manager with poll/stop.
- Doctor/diagnostics/export trajectory.
- Secrets vault and masking.
- Voice/realtime talk.
- Mobile gateway/client that Sandro can use away from the PC.
- Full “any app” learning with app maps and reusable app-specific skills.
- Benchmarks for lab improvements.
- Autonomous skill curator.
- Reliable public-action verification after X/email actions.

