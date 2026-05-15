param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8787
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$WebUrl = "http://$HostName`:$Port/"
$WebHealthUrl = "http://$HostName`:$Port/api/health"
$WebPidPath = Join-Path $RepoRoot "state\eve_web_pc2.pid"
$HealthPath = Join-Path $RepoRoot "state\eve_17_points_healthcheck.json"

Set-Location $RepoRoot

function Test-WebUi {
    try {
        $response = Invoke-WebRequest -Uri $WebHealthUrl -UseBasicParsing -TimeoutSec 5
        return [int]$response.StatusCode -eq 200
    } catch {
        return $false
    }
}

$branch = (& git branch --show-current 2>$null).Trim()
$commit = (& git log -1 --oneline 2>$null).Trim()
$webPid = $null
if (Test-Path $WebPidPath) {
    $webPid = (Get-Content -Raw $WebPidPath).Trim()
    if ($webPid -match "^\d+$") {
        $knownWebProcess = Get-Process -Id ([int]$webPid) -ErrorAction SilentlyContinue
        if (-not $knownWebProcess) {
            $webPid = $null
        }
    }
}

$telegram = $null
if (Test-Path $Python) {
    try {
        $telegramRaw = & $Python (Join-Path $RepoRoot "scripts\check_telegram_bridge.py")
        $telegram = $telegramRaw | ConvertFrom-Json
    } catch {
        $telegram = [pscustomobject]@{ ok = $false; running = $false; error = $_.Exception.Message }
    }
}

$health = $null
if (Test-Path $HealthPath) {
    try {
        $healthJson = Get-Content -Raw $HealthPath | ConvertFrom-Json
        $health = [ordered]@{
            overall_score = $healthJson.overall_score
            all_points_at_target = $healthJson.all_points_at_target
            timestamp = $healthJson.timestamp
        }
    } catch {
        $health = [ordered]@{ error = $_.Exception.Message }
    }
}

[ordered]@{
    ok = $true
    repo_root = $RepoRoot
    branch = $branch
    commit = $commit
    web_ui = [ordered]@{
        running = [bool](Test-WebUi)
        url = $WebUrl
        pid = $webPid
    }
    telegram_bridge = [ordered]@{
        running = [bool]$telegram.running
        pid = $telegram.pid
        token_configured = [bool]$telegram.token.configured
        last_update = $telegram.last_update
    }
    healthcheck = $health
} | ConvertTo-Json -Depth 6
