param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8787,
    [int]$TelegramInterval = 5,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$RuntimeLogDir = Join-Path $RepoRoot "logs\runtime"
$LogPath = Join-Path $RuntimeLogDir "eve_pc2_startup.log"
$WebPidPath = Join-Path $RepoRoot "state\eve_web_pc2.pid"
$WebOutLog = Join-Path $RuntimeLogDir "eve_web_pc2.out.log"
$WebErrLog = Join-Path $RuntimeLogDir "eve_web_pc2.err.log"
$WebUrl = "http://$HostName`:$Port/"
$WebHealthUrl = "http://$HostName`:$Port/api/health"

function Write-StartupLog {
    param([string]$Message)
    $stamp = (Get-Date).ToString("o")
    "[$stamp] $Message" | Tee-Object -FilePath $LogPath -Append | Out-Null
}

function Test-WebUi {
    param(
        [int]$Attempts = 1,
        [int]$DelaySeconds = 1
    )
    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $WebHealthUrl -UseBasicParsing -TimeoutSec 5
            if ([int]$response.StatusCode -eq 200) {
                return $true
            }
        } catch {
            if ($i -eq $Attempts) {
                Write-StartupLog "Web UI check failed after $Attempts attempt(s): $($_.Exception.Message)"
            }
        }
        if ($i -lt $Attempts) {
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    return $false
}

function Get-WebHealth {
    try {
        $response = Invoke-WebRequest -Uri $WebHealthUrl -UseBasicParsing -TimeoutSec 5
        if ([int]$response.StatusCode -eq 200) {
            return ($response.Content | ConvertFrom-Json)
        }
    } catch {
        return $null
    }
    return $null
}

function Stop-AllWebUiProcesses {
    $matches = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and
        $_.CommandLine -match "app[\\.]eve_web" -and
        $_.CommandLine -match "--port\s+$Port"
    }
    foreach ($item in $matches) {
        try {
            Write-StartupLog "Stopping old Web UI process PID $($item.ProcessId)"
            Stop-Process -Id $item.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {
            Write-StartupLog "Failed to stop old Web UI process PID $($item.ProcessId): $($_.Exception.Message)"
        }
    }
    Remove-Item -LiteralPath $WebPidPath -Force -ErrorAction SilentlyContinue
}

function Stop-AllTelegramBridgeProcesses {
    $matches = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine -match "scripts[\\/\\]telegram_bridge\.py\s+run"
    }
    foreach ($item in $matches) {
        try {
            Write-StartupLog "Stopping old Telegram Bridge process PID $($item.ProcessId)"
            Stop-Process -Id $item.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {
            Write-StartupLog "Failed to stop old Telegram Bridge process PID $($item.ProcessId): $($_.Exception.Message)"
        }
    }
    Remove-Item -LiteralPath (Join-Path $RepoRoot "state\telegram_bridge.pid") -Force -ErrorAction SilentlyContinue
}

function Stop-StaleWebUiProcesses {
    $matches = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and
        $_.CommandLine -match "app\.eve_web" -and
        $_.CommandLine -match "--port\s+$Port"
    }
    foreach ($item in $matches) {
        try {
            Write-StartupLog "Stopping stale Web UI process PID $($item.ProcessId)"
            Stop-Process -Id $item.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {
            Write-StartupLog "Failed to stop stale Web UI process PID $($item.ProcessId): $($_.Exception.Message)"
        }
    }
    Remove-Item -LiteralPath $WebPidPath -Force -ErrorAction SilentlyContinue
}

function Start-WebUiIfNeeded {
    Stop-AllWebUiProcesses
    Start-Sleep -Seconds 2
    Write-StartupLog "Starting Web UI at $WebUrl"
    $args = @("-m", "app.eve_web", "--host", $HostName, "--port", "$Port")
    $process = Start-Process -FilePath $Python -ArgumentList $args -WorkingDirectory $RepoRoot -RedirectStandardOutput $WebOutLog -RedirectStandardError $WebErrLog -PassThru -WindowStyle Hidden
    $process.Id | Set-Content -Path $WebPidPath -Encoding UTF8
    return @{ running = $false; started = $true; pid = $process.Id }
}

New-Item -ItemType Directory -Force -Path $RuntimeLogDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot "state") | Out-Null
Set-Location $RepoRoot

if (-not (Test-Path $Python)) {
    throw "Python venv not found: $Python"
}

Write-StartupLog "Starting Eve PC2 main runtime from $RepoRoot"
$webStart = Start-WebUiIfNeeded

Write-StartupLog "Stopping old Telegram Bridge before clean start"
& $Python (Join-Path $RepoRoot "scripts\telegram_bridge.py") stop 2>&1 | Tee-Object -FilePath $LogPath -Append
Stop-AllTelegramBridgeProcesses
Start-Sleep -Seconds 2
Write-StartupLog "Starting Telegram Bridge"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts\start_telegram_bridge.ps1") -Interval $TelegramInterval 2>&1 |
    Tee-Object -FilePath $LogPath -Append

Start-Sleep -Seconds 4
$webRunning = Test-WebUi -Attempts 6 -DelaySeconds 2
Write-StartupLog "Web UI running=$webRunning url=$WebUrl"

$telegramRaw = & $Python (Join-Path $RepoRoot "scripts\check_telegram_bridge.py")
$telegramRaw | Tee-Object -FilePath $LogPath -Append
$telegram = $telegramRaw | ConvertFrom-Json
Write-StartupLog "Telegram Bridge running=$($telegram.running)"

if ($webRunning) {
    $message = "Eve ligada no PC2. Web UI ativa em $WebUrl"
} else {
    $message = "Eve ligada no PC2, mas a Web UI nao respondeu em $WebUrl. Telegram Bridge ativa."
}
$notifyRaw = & $Python (Join-Path $RepoRoot "scripts\telegram_notify.py") $message
$notifyRaw | Tee-Object -FilePath $LogPath -Append
$notify = $notifyRaw | ConvertFrom-Json
Write-StartupLog "Telegram startup notification ok=$($notify.ok)"

try {
    Write-StartupLog "Writing startup awareness event"
    & $Python (Join-Path $RepoRoot "scripts\startup_awareness_event.py") 2>&1 | Tee-Object -FilePath $LogPath -Append
    & $Python (Join-Path $RepoRoot "scripts\heartbeat_once.py") 2>&1 | Tee-Object -FilePath $LogPath -Append
    & $Python (Join-Path $RepoRoot "scripts\awareness_snapshot.py") 2>&1 | Tee-Object -FilePath $LogPath -Append
} catch {
    Write-StartupLog "Awareness startup hook failed: $($_.Exception.Message)"
}

if ($webRunning -and -not $NoOpen) {
    try {
        Write-StartupLog "Opening Web UI in browser: $WebUrl"
        Start-Process $WebUrl | Out-Null
    } catch {
        Write-StartupLog "Failed to open Web UI in browser: $($_.Exception.Message)"
    }
}

$result = [ordered]@{
    ok = [bool]($webRunning -and $telegram.running)
    repo_root = $RepoRoot
    web_ui = [ordered]@{
        running = [bool]$webRunning
        url = $WebUrl
        started = [bool]$webStart.started
        pid = $webStart.pid
    }
    telegram_bridge = [ordered]@{
        running = [bool]$telegram.running
        pid = $telegram.pid
        token_configured = [bool]$telegram.token.configured
    }
    telegram_notification = [ordered]@{
        ok = [bool]$notify.ok
        message_id = $notify.message_id
        chat_id_present = [bool]$notify.chat_id_present
    }
    log = $LogPath
}

$result | ConvertTo-Json -Depth 6
