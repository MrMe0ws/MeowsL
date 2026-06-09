# Build MeowsL.exe with PyInstaller
# Run from project root: .\build\build.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location $Root

# Сначала `python` (GitHub Actions / venv), иначе `py -3` (локальный Windows).
# Заглушка Microsoft Store на `python` отсеивается пробным import.
$script:PythonLauncher = $null

function Test-PythonLauncher {
    param([string[]]$Launcher)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $out = & $launcher[0] $(if ($launcher.Length -gt 1) { $launcher[1..($launcher.Length - 1)] }) -c "import sys; print(sys.executable)" 2>&1
        return ($LASTEXITCODE -eq 0) -and ($out -match '[\\/]python')
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Get-PythonLauncher {
    if ($script:PythonLauncher) { return $script:PythonLauncher }
    foreach ($launcher in @(@("python"), @("py", "-3"))) {
        if (Test-PythonLauncher $launcher) {
            $script:PythonLauncher = $launcher
            return $launcher
        }
    }
    throw "Python 3 not found (tried: python, py -3)"
}

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $launcher = Get-PythonLauncher
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $launcher[0] $(if ($launcher.Length -gt 1) { $launcher[1..($launcher.Length - 1)] }) @Args
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed (exit $LASTEXITCODE): $($launcher -join ' ') $($Args -join ' ')"
        }
    } finally {
        $ErrorActionPreference = $prev
    }
}

Write-Host "==> Installing build dependencies..." -ForegroundColor Cyan
Invoke-Python -m pip install -r requirements.txt pyinstaller --quiet

Write-Host "==> Building exe..." -ForegroundColor Cyan
Invoke-Python -m PyInstaller build\meowsl.spec --noconfirm --clean

Write-Host ""
Write-Host "Done: dist\MeowsL.exe" -ForegroundColor Green
Write-Host ""
Write-Host "Installer (optional):" -ForegroundColor Yellow
Write-Host "  1. Install Inno Setup: https://jrsoftware.org/isinfo.php"
Write-Host "  2. Open build\installer.iss in Inno Setup Compiler"
Write-Host "  3. Build -> Compile -> dist\installer\MeowsL-Setup-0.2.0.exe"
