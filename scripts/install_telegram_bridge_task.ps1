param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ExpectedRoot = "E:\eve"
$TaskName = "Eve_Telegram_Bridge_PC2"
$StartScript = Join-Path $RepoRoot "scripts\start_telegram_bridge.ps1"

if ((Resolve-Path $RepoRoot).Path.ToLowerInvariant() -ne $ExpectedRoot.ToLowerInvariant()) {
    throw "Refusing to install PC2 Telegram bridge task outside $ExpectedRoot. Current root: $RepoRoot"
}

if (-not (Test-Path $StartScript)) {
    throw "Start script not found: $StartScript"
}

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing -and -not $Force) {
    Write-Output "Task already exists: $TaskName. Use -Force to replace it."
    exit 0
}

if ($existing -and $Force) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Starts the Eve Telegram bridge on PC2 at user logon." `
    -User $env:USERNAME | Out-Null

Write-Output "Installed scheduled task: $TaskName"
