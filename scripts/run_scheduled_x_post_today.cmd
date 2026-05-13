@echo off
setlocal
set "EVE_ROOT=%~dp0.."
for %%I in ("%EVE_ROOT%") do set "EVE_ROOT=%%~fI"
cd /d "%EVE_ROOT%"
python "%EVE_ROOT%\scripts\scheduled_x_post_today.py"
