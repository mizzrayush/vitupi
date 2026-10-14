<#
.SYNOPSIS
    Builds the standalone Vitupi Windows Executable and Setup Installer.

.DESCRIPTION
    Runs PyInstaller using vitupi.spec to produce dist/VitupiStudio.exe.
    If Inno Setup compiler (ISCC.exe) is present, compiles the setup wizard.
    Otherwise packages a portable ZIP archive ready for GitHub Releases.
#>

param (
    [switch]$SkipInno
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Vitupi Studio - Windows Executable & Installer Builder " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Virtual Environment
$PythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$PyInstallerExe = Join-Path $PSScriptRoot ".venv\Scripts\pyinstaller.exe"

if (-not (Test-Path $PyInstallerExe)) {
    Write-Host "PyInstaller not found. Installing into .venv..." -ForegroundColor Yellow
    & $PythonExe -m pip install pyinstaller
}

# 2. Run PyInstaller
Write-Host "`n[1/3] Compiling standalone VitupiStudio.exe with PyInstaller..." -ForegroundColor Green
& $PyInstallerExe --clean --noconfirm vitupi.spec

$OutputExe = Join-Path $PSScriptRoot "dist\VitupiStudio.exe"
if (-not (Test-Path $OutputExe)) {
    Write-Error "Failed to produce dist\VitupiStudio.exe"
    exit 1
}

$ExeSizeMB = [math]::Round((Get-Item $OutputExe).Length / 1MB, 2)
Write-Host "Success: Standalone executable created ($ExeSizeMB MB): $OutputExe" -ForegroundColor Green

# 3. Create Portable Zip
Write-Host "`n[2/3] Creating portable distribution ZIP archive..." -ForegroundColor Green
$ZipPath = Join-Path $PSScriptRoot "dist\VitupiStudio-v0.1.0-Windows-x64.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }

Compress-Archive -Path $OutputExe, (Join-Path $PSScriptRoot "README.md") -DestinationPath $ZipPath
$ZipSizeMB = [math]::Round((Get-Item $ZipPath).Length / 1MB, 2)
Write-Host "Success: Portable ZIP archive created ($ZipSizeMB MB): $ZipPath" -ForegroundColor Green

# 4. Check for Inno Setup compiler (ISCC)
Write-Host "`n[3/3] Checking for Inno Setup Compiler (ISCC.exe)..." -ForegroundColor Green

$InnoPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)

$IsccExe = $null
foreach ($p in $InnoPaths) {
    if (Test-Path $p) {
        $IsccExe = $p
        break
    }
}

if ($IsccExe -and (-not $SkipInno)) {
    Write-Host "Found Inno Setup at: $IsccExe" -ForegroundColor Cyan
    Write-Host "Compiling Windows Setup Wizard Installer..." -ForegroundColor Green
    & $IsccExe (Join-Path $PSScriptRoot "installer.iss")
    Write-Host "Installer compiled into dist\installer\" -ForegroundColor Green
} else {
    Write-Host "Inno Setup compiler (ISCC.exe) not found on system path." -ForegroundColor Yellow
    Write-Host "Portable bundle ready: $OutputExe" -ForegroundColor Green
    Write-Host "Portable archive ready: $ZipPath" -ForegroundColor Green
    Write-Host "(To build a wizard setup .exe, install Inno Setup 6 from https://jrsoftware.org/isdl.php)" -ForegroundColor Gray
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " Build Complete! Artifacts in dist\:" -ForegroundColor Cyan
Write-Host "  - Standalone EXE: dist\VitupiStudio.exe" -ForegroundColor White
Write-Host "  - Portable ZIP : dist\VitupiStudio-v0.1.0-Windows-x64.zip" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
