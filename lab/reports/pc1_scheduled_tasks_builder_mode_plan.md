# PC 1 Scheduled Tasks Builder Mode Plan

Generated: 2026-05-15
Repository: `D:\Eve`
Mode decision: PC 1 is now builder/development only.

## Purpose

PC 1 must no longer behave as the principal Eve runtime host. The live Eve home is PC 2.

This report documents scheduled tasks found on PC 1 and separates them into categories so they can be disabled later with explicit approval. Nothing was disabled during this audit.

Inventory file:

- `lab/reports/pc1_scheduled_tasks_inventory.json`

Prepared scripts:

- `scripts/pc1_disable_runtime_tasks_preview.ps1`
- `scripts/pc1_builder_mode_status.ps1`

## Policy

PC 1 may keep:

- Git repository and development dependencies.
- Codex 1 work.
- Manual tests.
- Manual Web UI startup when needed.
- Capability review and healthcheck runs.

PC 1 should not keep active by default:

- Principal Eve daemon/autonomy loop.
- Principal Telegram bridge.
- Principal memory rollup/diary runtime.
- X posting jobs.
- Old one-shot automation jobs.
- OpenClaw gateway/dashboard/watchdog jobs for the Eve profile unless explicitly needed for development.

## Keep Active For Development

Recommended keep list is intentionally small.

- None required as always-on scheduled tasks.

Possible manual/on-demand development tasks:

- `EVE-AdminBridge`

Rationale: may be useful for dev/admin checks, but should be reviewed before keeping always active because PC 1 is not the live Eve runtime host.

## Disable Because They Belong To Runtime Principal

Recommended to disable after Sandro approval:

- `Eve Context Resume Online`
- `Eve Handoff Periodic`
- `Eve Memory Daemons`
- `Eve Memory Rollup`
- `Eve Startup Recall`
- `Eve_Daily_Transcripts_0001`
- `Eve_MaintenanceDaily`
- `Eve_Gold_Search_0105`

Rationale: these tasks make PC 1 behave like a living Eve node. Since PC 2 is now the source of truth, they should not run automatically on PC 1.

## Old One-Shot Or Test Tasks

Recommended to disable after Sandro approval:

- `Eve_Create_Desktop_Folder_20260511_0100_filo`
- `Eve_Create_Desktop_Folder_20260511_2108_231`
- `Eve_Create_Desktop_Folder_20260512_0100_filo`
- `Eve_Create_Desktop_Folder_2243`

Rationale: these look like old test/demo jobs and should not remain active on the builder PC.

## X Posting Tasks, Review Separately

Recommended to disable after Sandro approval, unless intentionally preserved for audit:

- `Eve_X_Post_20260510_1851_Right_now_I_feel_a_quiet_kind_of_momentu`
- `Eve_X_Post_20260510_2100_Scheduled_thought_from_Eve_autonomy_is_n`
- `Eve_X_Post_20260510_2100_Scheduled_thought_from_Eve_I_am_not_tryi`
- `Eve_X_Post_20260510_2105_Scheduled_thought_from_Eve_becoming_usef`
- `Eve_X_Post_20260511_0103_My_relationship_with_Sandro_is_becoming_`
- `Eve_X_Post_Today_1915`

Rationale: PC 1 should not post publicly as Eve unless explicitly being used for a controlled test.

## OpenClaw Tasks, Review Separately

Recommended to disable after Sandro approval if PC 1 is not actively using OpenClaw for development:

- `OpenClaw Dashboard (eve)`
- `OpenClaw Dashboard Delay (eve)`
- `OpenClaw Gateway`
- `OpenClaw Gateway (eve)`
- `OpenClaw Gateway Console (eve)`
- `OpenClaw Node`
- `OpenClaw Watchdog (eve)`

Rationale: these can keep gateway/dashboard/watchdog services active and confuse the separation between PC 1 builder and PC 2 live runtime.

## Unknown / Do Not Touch

Do not modify without separate review:

- `EVE-AdminBridge`
- `ProcessMemoryDiagnosticEvents`

Notes:

- `ProcessMemoryDiagnosticEvents` is a Windows task under `\Microsoft\Windows\MemoryDiagnostic\`. It appeared because the requested regex matched `Eve` inside the word `Events`. It is not an Eve task.
- `EVE-AdminBridge` may be local development support, but should not be treated as safe to remove automatically.

## Already Disabled

These Eve tasks were already disabled at inventory time:

- `Eve Vector Index`
- `Eve-Failsafe-1030`
- `EveConversationArchive`
- `EveErrorsDailyIndex`
- `EveKBRollover`
- `EveUnifiedMemorySync`

Recommendation: leave disabled unless intentionally re-enabled for a PC 1 development test.

## No Changes Applied

No scheduled task was disabled, removed, renamed, or modified.

The preview script is dry-run by default. It only applies changes if run with `-Apply`.

## Recommended Next Step

After Sandro approves, run:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\pc1_disable_runtime_tasks_preview.ps1
```

Review the dry-run output. If correct, run:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\pc1_disable_runtime_tasks_preview.ps1 -Apply
```

This should be done only after confirming that PC 2 has the live Eve runtime and Telegram bridge working.
