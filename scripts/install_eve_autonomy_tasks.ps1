param(
    [string]$DailyLlmTime = "09:00",
    [switch]$EnableDailyLlm
)

$eveRoot = "D:\Eve"
$startupCmd = Join-Path $eveRoot "scripts\start_eve_interface.cmd"
$llmCmd = Join-Path $eveRoot "scripts\run_autonomy_cycle_llm.cmd"

schtasks /Create /TN "Eve_Console_And_Daemon_AtLogon" /SC ONLOGON /TR $startupCmd /F | Out-Host

if ($EnableDailyLlm) {
    schtasks /Create /TN "Eve_Daily_LLM_Self_Review" /SC DAILY /ST $DailyLlmTime /TR $llmCmd /F | Out-Host
} else {
    Write-Host "Daily LLM review task was not installed. Re-run with -EnableDailyLlm to schedule GPT-backed autonomy."
}
