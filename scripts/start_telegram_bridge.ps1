param(
    [int]$Interval = 5
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BridgeScript = Join-Path $RepoRoot "scripts\telegram_bridge.py"
$LogDir = Join-Path $RepoRoot "logs\telegram_bridge"
$StartLog = Join-Path $LogDir "start.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $RepoRoot

if (-not (Test-Path $Python)) {
    throw "Python venv not found: $Python"
}

if (-not (Test-Path $BridgeScript)) {
    throw "Telegram bridge script not found: $BridgeScript"
}

$timestamp = (Get-Date).ToString("o")
"[$timestamp] Starting Eve Telegram bridge from $RepoRoot with interval=$Interval" | Add-Content -Path $StartLog -Encoding UTF8

& $Python $BridgeScript start --interval $Interval 2>&1 | Tee-Object -FilePath $StartLog -Append
