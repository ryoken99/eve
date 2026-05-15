# PC2 Main Runtime Startup Setup

Generated: 2026-05-15

## Role

PC 2 is now treated as Eve's primary live installation.

- Repo root: `E:\eve`
- Web UI target: `http://127.0.0.1:8787/`
- Telegram Bridge: PC2 primary bridge
- Startup task target: `Eve_PC2_Main_Runtime`

## Scripts Created

- `scripts/start_eve_pc2.ps1`
  - Starts/checks the Web UI.
  - Starts/checks the Telegram Bridge.
  - Writes `logs\runtime\eve_pc2_startup.log`.
  - Sends a Telegram startup notification.
  - Avoids exposing the Telegram token.
  - Cleans stale `app.eve_web` processes on the target port before starting a fresh Web UI process.

- `scripts/stop_eve_pc2.ps1`
  - Stops the Telegram Bridge through the bridge CLI.
  - Stops the Web UI process only when a runtime PID file exists.
  - Writes to the runtime startup log.

- `scripts/status_eve_pc2.ps1`
  - Reports branch, last commit, Web UI status, Telegram Bridge status, healthcheck summary, and Web UI URL.

- `scripts/telegram_notify.py`
  - Sends a safe Telegram system notification using the token from the vault and the known Telegram chat id from local bridge state.
  - Does not print the full token.
  - Emits JSON with `ok`, `chat_id_present`, and `message_id` when successful.

- `scripts/create_eve_pc2_desktop_shortcut.ps1`
  - Creates `Abrir Eve PC2.lnk` on Sandro's Desktop.
  - Points to `powershell.exe -ExecutionPolicy Bypass -File "E:\eve\scripts\start_eve_pc2.ps1"`.

- `scripts/install_eve_pc2_startup_task.ps1`
  - Prepares the Windows logon scheduled task `Eve_PC2_Main_Runtime`.
  - Refuses to install outside `E:\eve`.
  - Does not store secrets/tokens in the task.

- `scripts/uninstall_eve_pc2_startup_task.ps1`
  - Removes the Windows logon task.

## Web UI Status

Manual startup was tested through:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_eve_pc2.ps1
```

Current result on this run:

- Web UI target: `http://127.0.0.1:8787/`
- Web UI confirmed HTTP 200: `false`
- Observed issue: port `8787` accumulated thousands of local `TIME_WAIT` entries during repeated runtime tests, and requests to `127.0.0.1:8787` timed out even after stale Web UI processes were stopped.
- Control check: the same Web UI module responded with HTTP `200` on alternate test ports, confirming the module itself can serve correctly.

Mitigation added:

- `app/eve_web.py` now reads only the tail of large transcript files for recent chat/activity endpoints.
- `app/eve_web.py` increased the HTTP request queue size.
- Web startup now cleans stale `app.eve_web` processes on the target port.
- Startup notification no longer claims the Web UI is active unless the HTTP check succeeds.

Expected next runtime condition:

- After the local TCP `TIME_WAIT` saturation clears, or after a Windows reboot, `start_eve_pc2.ps1` should be able to bind and verify `8787` normally.

## Telegram Status

Telegram Bridge status:

- Running: `true`
- Token configured: `true`, masked only
- Recent bridge check errors: none

Telegram startup notifications were sent successfully during testing.

- Last observed startup notification result: `ok: true`
- Last observed startup notification message ids included successful sends.

## Healthcheck

Executed:

```powershell
.\.venv\Scripts\python.exe scripts\full_eve_17_points_healthcheck.py
```

Result:

- Overall score: `10.0/10`
- All points at target: `true`
- Optional Telegram Bridge status: running

## Desktop Shortcut

Shortcut created:

```text
C:\Users\Sandro\Desktop\Abrir Eve PC2.lnk
```

Target:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "E:\eve\scripts\start_eve_pc2.ps1"
```

## Windows Startup Task

The startup task script was prepared but not installed automatically.

Install:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\install_eve_pc2_startup_task.ps1
```

Replace existing task:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\install_eve_pc2_startup_task.ps1 -Force
```

Uninstall:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\uninstall_eve_pc2_startup_task.ps1
```

## Secret/State Safety

Not for commit:

- `secrets/vault.json`
- `logs/`
- `state/telegram_bridge*`
- runtime PID files
- personal memory
- workspace

## Conclusion

PC2 now has official scripts for main Eve runtime startup, stop, status, Telegram notification, Desktop shortcut creation, and optional Windows logon task installation. Telegram Bridge is running and notification works. The only runtime gap observed in this test is the current local TCP saturation on port `8787`; the startup script now reports that honestly and avoids claiming Web UI success until HTTP verification passes.
