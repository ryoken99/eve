@echo off
cd /d D:\Eve
start "Eve Console" powershell -NoExit -ExecutionPolicy Bypass -Command "cd /d D:\Eve; python app\eve_codex.py chat"
start "Eve Daemon" /min powershell -WindowStyle Minimized -ExecutionPolicy Bypass -Command "cd /d D:\Eve; python scripts\eve_daemon.py --interval 900"
