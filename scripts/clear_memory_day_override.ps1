$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$OverridePath = Join-Path $RepoRoot "memory\runtime\session_state\memory_day_override.json"
$Today = Get-Date -Format "yyyy-MM-dd"

if (Test-Path $OverridePath) {
    Remove-Item -LiteralPath $OverridePath -Force
    Write-Host "Memory day override removed: $OverridePath"
} else {
    Write-Host "No memory day override found: $OverridePath"
}

Write-Host "Real local date: $Today"
Write-Host "New transcripts will use the real local date unless a new override is created."
