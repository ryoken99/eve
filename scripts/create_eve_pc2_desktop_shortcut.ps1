$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ExpectedRoot = $env:EVE_PC2_EXPECTED_ROOT
$StartScript = Join-Path $RepoRoot "scripts\start_eve_pc2.ps1"
$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Abrir Eve PC2.lnk"

if (-not [string]::IsNullOrWhiteSpace($ExpectedRoot) -and (Resolve-Path $RepoRoot).Path.ToLowerInvariant() -ne $ExpectedRoot.ToLowerInvariant()) {
    throw "Refusing to create PC2 shortcut outside $ExpectedRoot. Current root: $RepoRoot"
}

if (-not (Test-Path $StartScript)) {
    throw "Start script not found: $StartScript"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
$shortcut.WorkingDirectory = $RepoRoot
$iconCandidate = Join-Path $RepoRoot "assets\eve.ico"
if (Test-Path $iconCandidate) {
    $shortcut.IconLocation = $iconCandidate
} else {
    $shortcut.IconLocation = "powershell.exe,0"
}
$shortcut.Description = "Abrir Eve PC2"
$shortcut.Save()

[ordered]@{
    ok = $true
    shortcut = $ShortcutPath
    target = $shortcut.TargetPath
    arguments = $shortcut.Arguments
    working_directory = $shortcut.WorkingDirectory
} | ConvertTo-Json -Depth 4
