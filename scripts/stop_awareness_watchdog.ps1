$ErrorActionPreference = "Stop"
$matches = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match "awareness_watchdog\.py"
}
foreach ($item in $matches) {
    Write-Host "Stopping awareness watchdog PID $($item.ProcessId)"
    Stop-Process -Id $item.ProcessId -Force -ErrorAction SilentlyContinue
}
if (-not $matches) {
    Write-Host "No awareness watchdog process found."
}
