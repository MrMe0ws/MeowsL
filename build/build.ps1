# Build MeowsL.exe with PyInstaller
# Run from project root: .\build\build.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location $Root

$script:PythonExe = $null

function Get-PythonExe {
    if ($script:PythonExe) { return $script:PythonExe }

    $candidates = @("python", "py")
    foreach ($cmd in $candidates) {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "SilentlyContinue"
        try {
            if ($cmd -eq "py") {
                $out = & py -3 -c "import sys; print(sys.executable)" 2>&1
            } else {
                $out = & python -c "import sys; print(sys.executable)" 2>&1
            }
            if ($LASTEXITCODE -eq 0 -and $out -match '[\\/]python\.exe$') {
                $script:PythonExe = $out.ToString().Trim()
                return $script:PythonExe
            }
        } finally {
            $ErrorActionPreference = $prev
        }
    }

    throw "Python 3 not found (tried: python, py -3)"
}

function Invoke-Python {
    param([string[]]$PythonArgs)
    $exe = Get-PythonExe
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $exe @PythonArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed (exit $LASTEXITCODE): $exe $($PythonArgs -join ' ')"
        }
    } finally {
        $ErrorActionPreference = $prev
    }
}

Write-Host "==> Python: $(Get-PythonExe)" -ForegroundColor Cyan
Write-Host "==> Installing build dependencies..." -ForegroundColor Cyan
Invoke-Python @("-m", "pip", "install", "-r", "requirements.txt", "pyinstaller", "--quiet")

Write-Host "==> Building exe..." -ForegroundColor Cyan
Invoke-Python @("-m", "PyInstaller", "build\meowsl.spec", "--noconfirm", "--clean")

if (-not (Test-Path "dist\MeowsL.exe")) {
    throw "dist\MeowsL.exe not found after PyInstaller"
}

$versionMatch = Select-String -Path "src\translate_meows\config.py" -Pattern 'APP_VERSION\s*=\s*"([^"]+)"' | Select-Object -First 1
if (-not $versionMatch) {
    throw "APP_VERSION not found in src\translate_meows\config.py"
}
$version = $versionMatch.Matches[0].Groups[1].Value
$versionedExe = "dist\MeowsL_$version.exe"
Copy-Item "dist\MeowsL.exe" $versionedExe -Force

Write-Host ""
Write-Host "Done: $versionedExe" -ForegroundColor Green
Write-Host "Also: dist\MeowsL.exe (for installer)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Installer (optional):" -ForegroundColor Yellow
Write-Host "  1. Install Inno Setup: https://jrsoftware.org/isinfo.php"
Write-Host "  2. Open build\installer.iss in Inno Setup Compiler"
Write-Host "  3. Build -> Compile -> dist\installer\MeowsL-Setup.exe"
