@echo off
setlocal

net session >nul 2>&1
if not "%errorlevel%"=="0" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

cd /d D:\Eve
start "Eve Web" /min powershell.exe -WindowStyle Minimized -ExecutionPolicy Bypass -Command "Set-Location D:\Eve; python app\eve_web.py --host 127.0.0.1 --port 8787 --open"
start "Eve Daemon" /min powershell.exe -WindowStyle Minimized -ExecutionPolicy Bypass -Command "Set-Location D:\Eve; python scripts\eve_daemon.py --interval 900"
