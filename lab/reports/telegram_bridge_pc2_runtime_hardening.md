# Telegram Bridge PC2 Runtime Hardening

Generated: 2026-05-15

## PC2 Runtime Role

PC 2 is now treated as Eve's primary local installation.

- Repo root: `E:\eve`
- Runtime target: PC2
- Web UI target: local Eve Web UI
- Telegram bridge target: local long-running bridge
- Token policy: token remains in local secrets vault only; reports and scripts must only show masked status.

## Current Bridge Status

The Telegram bridge status check is available and returns safe JSON.

- Bridge tools module exists: `tools/telegram_bridge.py`
- Bridge CLI wrapper exists: `scripts/telegram_bridge.py`
- Token secret key exists: `telegram_eveh_by_r_bot_token`
- Token output policy: masked only
- Last verified running state: `true`
- Last verified PID: recorded by local runtime status
- Last update: recorded by local runtime status

## Added Runtime Scripts

- `scripts/start_telegram_bridge.ps1`
  - Resolves the repo root dynamically from the script location.
  - Uses `.venv\Scripts\python.exe`.
  - Starts `scripts\telegram_bridge.py start --interval 5`.
  - Creates `logs\telegram_bridge`.
  - Writes startup output to `logs\telegram_bridge\start.log`.
  - Does not print or read the full token directly.

- `scripts/stop_telegram_bridge.ps1`
  - Uses the repo venv.
  - Calls `scripts\telegram_bridge.py stop`.

- `scripts/check_telegram_bridge.ps1`
  - Uses the repo venv.
  - Calls `scripts\telegram_bridge.py status`.

- `scripts/check_telegram_bridge.py`
  - Confirms bridge scripts exist.
  - Confirms the Telegram token secret key exists, without revealing the token.
  - Calls bridge status.
  - Emits JSON with `running`, `pid`, `last_update`, masked token status, and recent bridge errors.

- `scripts/install_telegram_bridge_task.ps1`
  - Prepares an optional Windows scheduled task named `Eve_Telegram_Bridge_PC2`.
  - Runs at user logon.
  - Calls `scripts\start_telegram_bridge.ps1`.
  - Refuses to install outside `E:\eve` to avoid accidental PC1 installation.
  - Supports `-Force` to replace an existing task.

## Healthcheck Integration

`scripts/full_eve_17_points_healthcheck.py` now includes optional `telegram_bridge_status`.

This status:

- Does not affect the 17-point runtime score.
- Does not fail the healthcheck if the bridge is stopped.
- Warns if the bridge is unavailable, stopped, or returns an error.
- Records masked token configuration status only.

## Validation Run

Executed:

```powershell
.\.venv\Scripts\python.exe scripts\check_telegram_bridge.py
.\.venv\Scripts\python.exe scripts\full_eve_17_points_healthcheck.py
```

Observed result:

- Telegram bridge check: passed.
- Telegram bridge running: true.
- Token configured: true, masked only.
- Recent bridge errors: none in the bridge check output.
- Full 17-point healthcheck: passed.
- Overall healthcheck score: `10.0/10`.
- All points at target: true.
- Optional `telegram_bridge_status` included in the generated state and Markdown report.

## Scheduled Task State

The Windows scheduled task installer was prepared but not executed automatically.

Reason: task installation changes machine startup behavior. It should be explicitly run when Sandro wants Telegram to start on Windows logon.

Command:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\install_telegram_bridge_task.ps1
```

Replace existing task:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\install_telegram_bridge_task.ps1 -Force
```

## Risks And Notes

- `scripts\telegram_bridge.py start` can create a launcher process and a child Python process on Windows. The bridge status should be treated as authoritative because it reads the PID state used by the bridge.
- Runtime logs in `logs\telegram_bridge\` are local operational files and should not be committed.
- State files such as `state\telegram_bridge.pid` and `state\telegram_bridge_state.json` are local runtime state and should not be committed.
- `secrets\vault.json` must never be committed.

## Safe Restore Commands

Check:

```powershell
.\.venv\Scripts\python.exe scripts\check_telegram_bridge.py
```

Start:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_telegram_bridge.ps1
```

Stop:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\stop_telegram_bridge.ps1
```

Raw bridge status:

```powershell
.\.venv\Scripts\python.exe scripts\telegram_bridge.py status
```

## Conclusion

The PC2 Telegram bridge now has official start, stop, check, healthcheck visibility, and an optional Windows task installer. Secrets remain local and masked; runtime logs and state remain uncommitted.
