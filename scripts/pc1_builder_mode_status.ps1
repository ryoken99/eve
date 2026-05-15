$ErrorActionPreference = "Continue"

Write-Host "PC 1 Builder/Dev Mode Status"
Write-Host "WARNING: PC 1 is not the principal Eve runtime host. PC 2 is the live Eve home."
Write-Host ""

Write-Host "Repository"
try {
    $branch = git branch --show-current
    $commit = git log -1 --oneline
    Write-Host "  Branch: $branch"
    Write-Host "  Last commit: $commit"
} catch {
    Write-Host "  Git status unavailable: $($_.Exception.Message)"
}
Write-Host ""

Write-Host "Eve/Python/Telegram/Daemon processes"
try {
    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -match "D:\\Eve|telegram|bridge|daemon|python"
    } | Select-Object ProcessId, CommandLine

    if ($processes) {
        $processes | Format-Table -AutoSize | Out-String -Width 300 | Write-Host
    } else {
        Write-Host "  No matching Eve/Python/Telegram/Daemon process found."
    }
} catch {
    Write-Host "  Process check failed: $($_.Exception.Message)"
}
Write-Host ""

Write-Host "Scheduled tasks matching Eve/OpenClaw/Telegram/Bridge/Daemon"
try {
    Get-ScheduledTask | Where-Object {
        $_.TaskName -match "Eve|OpenClaw|telegram|bridge|daemon"
    } | Select-Object TaskName, State, TaskPath | Sort-Object TaskName | Format-Table -AutoSize | Out-String -Width 300 | Write-Host
} catch {
    Write-Host "  Scheduled task check failed: $($_.Exception.Message)"
}
Write-Host ""

Write-Host "Web UI check"
try {
    $uiPorts = @(8787, 8000, 8080, 5000)
    $listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {
        $uiPorts -contains $_.LocalPort
    } | Select-Object LocalAddress, LocalPort, OwningProcess

    if ($listeners) {
        $listeners | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
    } else {
        Write-Host "  No common Eve Web UI port is listening: 8787, 8000, 8080, 5000."
    }
} catch {
    Write-Host "  Web UI port check failed: $($_.Exception.Message)"
}
Write-Host ""

Write-Host "Telegram bridge check"
try {
    $telegramProcesses = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -match "telegram_bridge|Telegram|telegram"
    } | Select-Object ProcessId, CommandLine

    if ($telegramProcesses) {
        $telegramProcesses | Format-Table -AutoSize | Out-String -Width 300 | Write-Host
    } else {
        Write-Host "  No Telegram bridge process found."
    }
} catch {
    Write-Host "  Telegram bridge check failed: $($_.Exception.Message)"
}
Write-Host ""

Write-Host "Reminder"
Write-Host "  Keep PC 1 for development/build/test. Do not run main daemon, Telegram bridge, or 24/7 autonomy here by default."
