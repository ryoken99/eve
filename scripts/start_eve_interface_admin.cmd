@echo off
setlocal
set "EVE_ROOT=%~dp0.."
for %%I in ("%EVE_ROOT%") do set "EVE_ROOT=%%~fI"

net session >nul 2>&1
if not "%errorlevel%"=="0" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

cd /d "%EVE_ROOT%"
start "Eve Web" /min powershell.exe -WindowStyle Minimized -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%EVE_ROOT%'; python app\eve_web.py --host 127.0.0.1 --port 8787 --open"
start "Eve Daemon" /min powershell.exe -WindowStyle Minimized -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%EVE_ROOT%'; python scripts\eve_daemon.py --interval 30"
