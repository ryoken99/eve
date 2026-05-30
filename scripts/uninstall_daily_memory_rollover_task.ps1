$ErrorActionPreference = "Continue"
$TaskName = "Eve_Daily_Memory_Rollover_PC2"
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
[ordered]@{
    ok = $true
    removed = $TaskName
} | ConvertTo-Json -Depth 4
