param(
    [int]$IntervalSeconds = 300
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Policy = Join-Path $RepoRoot "memory\_system\awareness_watchdog_policy.yaml"

if (-not (Test-Path $Python)) { throw "Python venv not found: $Python" }
if (-not (Test-Path $Policy)) { throw "Policy not found: $Policy" }

$policyText = Get-Content -Raw $Policy
if ($policyText -notmatch "enabled:\s*true") {
    Write-Host "Awareness watchdog is prepared but disabled by policy. Not starting."
    exit 0
}

Start-Process -FilePath $Python -ArgumentList @("scripts\awareness_watchdog.py", "--interval", "$IntervalSeconds") -WorkingDirectory $RepoRoot -WindowStyle Hidden
Write-Host "Awareness watchdog start requested."
