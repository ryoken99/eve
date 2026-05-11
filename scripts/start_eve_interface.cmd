@echo off
cd /d D:\Eve
start "Eve Web" /min powershell -WindowStyle Minimized -ExecutionPolicy Bypass -Command "Set-Location D:\Eve; python app\eve_web.py --host 127.0.0.1 --port 8787 --open"
start "Eve Daemon" /min powershell -WindowStyle Minimized -ExecutionPolicy Bypass -Command "Set-Location D:\Eve; python scripts\eve_daemon.py --interval 30"
