param(
    [string]$EveRoot = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

$EveRoot = (Resolve-Path -LiteralPath $EveRoot).Path
$LogDir = Join-Path $EveRoot "logs"
$ConfigDir = Join-Path $EveRoot "config"
$DataDir = Join-Path $EveRoot "data"
$MemoryDir = Join-Path $EveRoot "memory"
$ScriptsDir = Join-Path $EveRoot "scripts"
$TasksDir = Join-Path $EveRoot "tasks"
$BackupDir = Join-Path $EveRoot "backups"
$AppDir = Join-Path $EveRoot "app"
$SecretsDir = Join-Path $EveRoot "secrets"
$EveCodex = Join-Path $AppDir "eve_codex.py"

foreach ($dir in @($LogDir, $ConfigDir, $DataDir, $MemoryDir, $ScriptsDir, $TasksDir, $BackupDir, $AppDir, $SecretsDir)) {
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
}

function Write-EveHeader {
    Clear-Host
    Write-Host ""
    Write-Host "========================================" -ForegroundColor DarkCyan
    Write-Host " Eve - Local Agent Console" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor DarkCyan
    Write-Host " Eve:     $EveRoot" -ForegroundColor DarkGray
    Write-Host " Auth:    Eve Codex OAuth proprio" -ForegroundColor DarkGray
    Write-Host " Backend: Eve Python client" -ForegroundColor DarkGray
    Write-Host ""
}

function Invoke-EvePython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    python $EveCodex @Arguments
}

function Pause-Eve {
    Write-Host ""
    Read-Host "Enter para continuar"
}

function Show-Status {
    Write-EveHeader
    Write-Host "Estado do Windows:" -ForegroundColor Yellow
    Get-PSDrive C, D | Select-Object Name, @{Name="FreeGB";Expression={[math]::Round($_.Free / 1GB, 2)}} | Format-Table -AutoSize

    Write-Host ""
    Write-Host "Estado do WSL:" -ForegroundColor Yellow
    wsl -l -v

    Write-Host ""
    Write-Host "Eve Codex OAuth:" -ForegroundColor Yellow
    Invoke-EvePython @("status")

    Pause-Eve
}

function Login-Codex {
    Write-EveHeader
    Write-Host "Login OpenAI Codex / ChatGPT OAuth da Eve" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Vai aparecer um link/codigo. Autentica com a tua conta OpenAI/ChatGPT." -ForegroundColor Gray
    Write-Host "Este login e proprio da Eve; nao usa Hermes, OpenClaw nem copia tokens internos." -ForegroundColor Gray
    Write-Host ""
    Invoke-EvePython @("login")
    Write-Host ""
    Write-Host "Login concluido. Chat disponivel." -ForegroundColor Green
    Start-Sleep -Seconds 1
    Open-Chat
}

function Start-Eve {
    if (Test-Path -LiteralPath (Join-Path $SecretsDir "codex_auth.json")) {
        Open-Chat
        return
    }

    Login-Codex
}

function Configure-Model {
    Write-EveHeader
    Write-Host "Configurar modelo Codex da Eve" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Modelo atual recomendado: gpt-5.4" -ForegroundColor Gray
    Write-Host ""
    $model = Read-Host "Modelo"
    if (-not [string]::IsNullOrWhiteSpace($model)) {
        Invoke-EvePython @("model", $model)
    }
    Pause-Eve
}

function Open-Chat {
    Write-EveHeader
    Write-Host "A abrir chat com a Eve..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Dentro do chat, escreve a mensagem. Usa /sair para voltar ao menu." -ForegroundColor Gray
    Write-Host ""
    Invoke-EvePython @("chat")
    Pause-Eve
}

function Open-OneShot {
    Write-EveHeader
    Write-Host "Pergunta unica para a Eve" -ForegroundColor Yellow
    Write-Host ""
    $prompt = Read-Host "Escreve a pergunta"
    if ([string]::IsNullOrWhiteSpace($prompt)) {
        return
    }

    Invoke-EvePython @("ask", $prompt)
    Pause-Eve
}

function Open-ConfigFolder {
    Start-Process explorer.exe $EveRoot
}

Start-Eve
