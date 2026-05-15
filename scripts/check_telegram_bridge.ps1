$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BridgeScript = Join-Path $RepoRoot "scripts\telegram_bridge.py"

Set-Location $RepoRoot

if (-not (Test-Path $Python)) {
    throw "Python venv not found: $Python"
}

if (-not (Test-Path $BridgeScript)) {
    throw "Telegram bridge script not found: $BridgeScript"
}

& $Python $BridgeScript status
