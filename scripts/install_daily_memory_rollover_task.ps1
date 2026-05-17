$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$TaskName = "Eve_Daily_Memory_Rollover_PC2"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Rollover = Join-Path $RepoRoot "scripts\daily_memory_rollover.py"

if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
if (-not (Test-Path $Rollover)) { throw "Rollover script not found: $Rollover" }

$action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Rollover`"" -WorkingDirectory $RepoRoot
$trigger = New-ScheduledTaskTrigger -Daily -At "00:00"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Runs Eve PC2 daily memory rollover at midnight." -Force | Out-Null

[ordered]@{
    ok = $true
    task_name = $TaskName
    schedule = "daily 00:00"
    command = "$Python $Rollover"
    working_directory = $RepoRoot
} | ConvertTo-Json -Depth 4
