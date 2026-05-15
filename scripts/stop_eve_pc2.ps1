$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$RuntimeLogDir = Join-Path $RepoRoot "logs\runtime"
$LogPath = Join-Path $RuntimeLogDir "eve_pc2_startup.log"
$WebPidPath = Join-Path $RepoRoot "state\eve_web_pc2.pid"

function Write-StopLog {
    param([string]$Message)
    $stamp = (Get-Date).ToString("o")
    "[$stamp] $Message" | Tee-Object -FilePath $LogPath -Append
}

New-Item -ItemType Directory -Force -Path $RuntimeLogDir | Out-Null
Set-Location $RepoRoot

Write-StopLog "Stopping Eve PC2 runtime"
if (Test-Path $Python) {
    & $Python (Join-Path $RepoRoot "scripts\telegram_bridge.py") stop 2>&1 | Tee-Object -FilePath $LogPath -Append
} else {
    Write-StopLog "Python venv not found; skipping Telegram Bridge stop."
}

$webStopped = $false
if (Test-Path $WebPidPath) {
    $pidText = (Get-Content -Raw $WebPidPath).Trim()
    if ($pidText -match "^\d+$") {
        $process = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id ([int]$pidText) -Force -ErrorAction SilentlyContinue
            $webStopped = $true
            Write-StopLog "Stopped Web UI PID $pidText"
        }
    }
    Remove-Item -LiteralPath $WebPidPath -Force -ErrorAction SilentlyContinue
}

[ordered]@{
    ok = $true
    telegram_stop_requested = $true
    web_stopped = $webStopped
    log = $LogPath
} | ConvertTo-Json -Depth 4
