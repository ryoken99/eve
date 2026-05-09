from __future__ import annotations

import sys

from core.paths import EVE_ROOT
from tools.windows_scheduler import create_daily_task


def install_startup_daemon_task(*, time_hhmm: str = "09:00") -> dict:
    command = f'"{sys.executable}" "{EVE_ROOT / "app" / "eve_codex.py"}" daemon-tick'
    return create_daily_task("Eve_Autonomy_Daemon_Tick", time_hhmm, command)


def install_startup_console_task(*, time_hhmm: str = "09:01") -> dict:
    command = f'Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File ""{EVE_ROOT / "Start-Eve.ps1"}"""'
    return create_daily_task("Eve_Open_Console", time_hhmm, command)

