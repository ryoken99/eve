# PC 1 Builder Mode Application Attempt

Generated: 2026-05-15
Repository: `D:\Eve`
Branch: `main`

## Decision

PC 1 is now designated as builder/development only. PC 2 is the principal runtime home and source of truth for Eve's live state.

This run attempted to disable the authorized PC 1 runtime scheduled tasks, but the current PowerShell session was not elevated as administrator. Windows returned `Access denied` when `Disable-ScheduledTask` was called.

No scheduled task was deleted.

## Administrator Status

The current session is not elevated:

```text
IsAdministrator: False
```

Observed failure:

```text
Disable-ScheduledTask : Acesso negado.
```

## Backup

The scheduled tasks were exported before the disable attempt.

Backup location:

```text
D:\Eve\backups\pc1_scheduled_tasks_before_builder_mode
```

Files exported:

- `tasks_inventory.json`
- one XML export for each matching task found by `Eve|OpenClaw|telegram|bridge|daemon`

The backup/export step completed before the permission failure.

## Tasks Intended For Disable

The following runtime Eve tasks were intended to be disabled, but remain unchanged because the session lacked administrator privileges:

- `Eve Context Resume Online`
- `Eve Handoff Periodic`
- `Eve Memory Daemons`
- `Eve Memory Rollup`
- `Eve Startup Recall`
- `Eve_Daily_Transcripts_0001`
- `Eve_Gold_Search_0105`
- `Eve_MaintenanceDaily`

The following old test tasks were also intended to be disabled, but remain unchanged:

- `Eve_Create_Desktop_Folder_20260511_0100_filo`
- `Eve_Create_Desktop_Folder_20260511_2108_231`
- `Eve_Create_Desktop_Folder_20260512_0100_filo`
- `Eve_Create_Desktop_Folder_2243`

## Tasks Explicitly Not Modified

These were intentionally not touched:

- `Eve_X_Post_*`
- `OpenClaw Dashboard/Gateway/Node/Watchdog`
- `EVE-AdminBridge`
- `ProcessMemoryDiagnosticEvents`

## Final Task State

The tasks still showed as `Ready` after the failed disable attempt:

- `Eve Context Resume Online`
- `Eve Handoff Periodic`
- `Eve Memory Daemons`
- `Eve Memory Rollup`
- `Eve Startup Recall`
- `Eve_Create_Desktop_Folder_20260511_0100_filo`
- `Eve_Create_Desktop_Folder_20260511_2108_231`
- `Eve_Create_Desktop_Folder_20260512_0100_filo`
- `Eve_Create_Desktop_Folder_2243`
- `Eve_Daily_Transcripts_0001`
- `Eve_Gold_Search_0105`
- `Eve_MaintenanceDaily`

Previously disabled Eve maintenance/archive tasks remained disabled:

- `Eve Vector Index`
- `EveConversationArchive`
- `EveErrorsDailyIndex`
- `Eve-Failsafe-1030`
- `EveKBRollover`
- `EveUnifiedMemorySync`

## Processes Found

The process check did not identify a clear active Eve Python daemon or Telegram bridge process. Matches were from:

- Codex desktop processes.
- Razer/CefSharp background processes.
- Temporary PowerShell commands used by the audit.

No process was stopped.

## Builder Mode Status

Conceptually, PC 1 is builder/development only. Operationally, old scheduled tasks still need to be disabled from an elevated PowerShell/admin session.

Codex 1 remains ready to:

- build Eve;
- update the repo;
- run tests;
- prepare PRs;
- inspect and improve architecture;
- support PC 2 as the principal runtime host.

## Required Next Step

Run the prepared dry-run script from an elevated/admin PowerShell first:

```powershell
cd D:\Eve
powershell.exe -ExecutionPolicy Bypass -File .\scripts\pc1_disable_runtime_tasks_preview.ps1
```

Then, if the preview is correct, run:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\pc1_disable_runtime_tasks_preview.ps1 -Apply
```

This should disable the approved runtime/test tasks only. It will not change X posting tasks, OpenClaw tasks, `EVE-AdminBridge`, or `ProcessMemoryDiagnosticEvents`.
