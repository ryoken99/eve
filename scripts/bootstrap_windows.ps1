param(
    [string]$EveRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path,
    [string]$Python = "python",
    [string]$InstallName = "local",
    [string]$AccessCode = "",
    [switch]$CreateVenv,
    [switch]$InstallPlaywright,
    [switch]$ConfigureLocalAccount,
    [switch]$AddSandroPcProfiles,
    [switch]$SkipPip
)

$ErrorActionPreference = "Stop"

$EveRoot = (Resolve-Path -LiteralPath $EveRoot).Path
$venvPython = Join-Path $EveRoot ".venv\Scripts\python.exe"

Write-Host "Eve bootstrap" -ForegroundColor Cyan
Write-Host "Root: $EveRoot" -ForegroundColor DarkGray

if ($CreateVenv) {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host "Creating .venv..." -ForegroundColor Yellow
        & $Python -m venv (Join-Path $EveRoot ".venv")
    }
    $Python = $venvPython
}

& $Python --version | Out-Host

if (-not $SkipPip) {
    Write-Host "Installing Python requirements..." -ForegroundColor Yellow
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r (Join-Path $EveRoot "requirements.txt")
}

if ($InstallPlaywright) {
    Write-Host "Installing Playwright Chromium..." -ForegroundColor Yellow
    & $Python -m playwright install chromium
}

if ($ConfigureLocalAccount) {
    if ([string]::IsNullOrWhiteSpace($AccessCode)) {
        $secure = Read-Host "Define a pass/codigo de entrada da Eve" -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try {
            $AccessCode = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        } finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
    Write-Host "Configuring local Eve account/profile..." -ForegroundColor Yellow
    $args = @(
        "-m", "security.local_account", "configure",
        "--install-name", $InstallName,
        "--install-root", $EveRoot
    )
    if (-not [string]::IsNullOrWhiteSpace($AccessCode)) {
        $args += @("--access-code", $AccessCode)
    }
    if ($AddSandroPcProfiles) {
        $args += "--add-sandro-defaults"
    }
    & $Python @args
}

Write-Host "Creating local directories..." -ForegroundColor Yellow
& $Python -c "from core.paths import ensure_project_dirs; ensure_project_dirs(); print('project dirs ok')"

Write-Host ""
Write-Host "Bootstrap complete." -ForegroundColor Green
Write-Host "Next checks:" -ForegroundColor Cyan
Write-Host "  $Python scripts\check_fresh_clone_readiness.py"
Write-Host "  $Python -m pytest"
Write-Host "  $Python scripts\run_capability_tests.py"
Write-Host "  $Python scripts\full_eve_healthcheck.py"
Write-Host ""
Write-Host "Optional external dependency for OCR:" -ForegroundColor Cyan
Write-Host "  Install Tesseract OCR and make tesseract.exe available on PATH."
