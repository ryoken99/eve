param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

Write-Host "PC 1 builder/dev mode scheduled task preview"
Write-Host "PC 1 is not the principal Eve runtime host."
Write-Host "Default mode: dry-run. Use -Apply to disable the recommended runtime tasks."
Write-Host ""

$runtimeTasks = @(
    "Eve Context Resume Online",
    "Eve Handoff Periodic",
    "Eve Memory Daemons",
    "Eve Memory Rollup",
    "Eve Startup Recall",
    "Eve_Daily_Transcripts_0001",
    "Eve_Gold_Search_0105",
    "Eve_MaintenanceDaily",
    "Eve_Create_Desktop_Folder_20260511_0100_filo",
    "Eve_Create_Desktop_Folder_20260511_2108_231",
    "Eve_Create_Desktop_Folder_20260512_0100_filo",
    "Eve_Create_Desktop_Folder_2243"
)

$xPostingTasks = @(
    "Eve_X_Post_20260510_1851_Right_now_I_feel_a_quiet_kind_of_momentu",
    "Eve_X_Post_20260510_2100_Scheduled_thought_from_Eve_autonomy_is_n",
    "Eve_X_Post_20260510_2100_Scheduled_thought_from_Eve_I_am_not_tryi",
    "Eve_X_Post_20260510_2105_Scheduled_thought_from_Eve_becoming_usef",
    "Eve_X_Post_20260511_0103_My_relationship_with_Sandro_is_becoming_",
    "Eve_X_Post_Today_1915"
)

$openClawTasks = @(
    "OpenClaw Dashboard (eve)",
    "OpenClaw Dashboard Delay (eve)",
    "OpenClaw Gateway",
    "OpenClaw Gateway (eve)",
    "OpenClaw Gateway Console (eve)",
    "OpenClaw Node",
    "OpenClaw Watchdog (eve)"
)

$unknownDoNotTouch = @(
    "EVE-AdminBridge",
    "ProcessMemoryDiagnosticEvents"
)

function Show-TaskGroup {
    param(
        [string]$Title,
        [string[]]$TaskNames
    )

    Write-Host $Title
    foreach ($name in $TaskNames) {
        $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        if ($null -eq $task) {
            Write-Host "  [missing] $name"
            continue
        }
        Write-Host ("  [{0}] {1}" -f $task.State, $task.TaskName)
    }
    Write-Host ""
}

Show-TaskGroup "Recommended runtime tasks to disable on PC 1:" $runtimeTasks
Show-TaskGroup "X posting tasks to review separately:" $xPostingTasks
Show-TaskGroup "OpenClaw tasks to review separately:" $openClawTasks
Show-TaskGroup "Unknown / do not touch automatically:" $unknownDoNotTouch

if (-not $Apply) {
    Write-Host "Dry-run only. No scheduled tasks were changed."
    exit 0
}

Write-Host "Apply mode enabled. Disabling recommended runtime tasks only."
foreach ($name in $runtimeTasks) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        Write-Host "  [missing] $name"
        continue
    }
    if ($task.State -eq "Disabled") {
        Write-Host "  [already disabled] $name"
        continue
    }
    Disable-ScheduledTask -TaskName $name | Out-Null
    Write-Host "  [disabled] $name"
}

Write-Host ""
Write-Host "Finished. X posting, OpenClaw, and unknown tasks were not changed."
