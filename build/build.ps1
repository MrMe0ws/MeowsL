# Build MeowsL.exe with PyInstaller
# Run from project root: .\build\build.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location $Root

Write-Host "==> Installing build dependencies..." -ForegroundColor Cyan
py -3 -m pip install -r requirements.txt pyinstaller --quiet

Write-Host "==> Building exe..." -ForegroundColor Cyan
py -3 -m PyInstaller build\meowsl.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Done: dist\MeowsL.exe" -ForegroundColor Green
Write-Host ""
Write-Host "Installer (optional):" -ForegroundColor Yellow
Write-Host "  1. Install Inno Setup: https://jrsoftware.org/isinfo.php"
Write-Host "  2. Open build\installer.iss in Inno Setup Compiler"
Write-Host "  3. Build -> Compile -> dist\installer\MeowsL-Setup-0.2.0.exe"
