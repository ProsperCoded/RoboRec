# Build RoboRec with Nuitka into a single Windows executable
param(
    [switch]$Clean = $true
)

$ErrorActionPreference = "Stop"

$REPO_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $REPO_ROOT

Write-Host "🔨 Building RoboRec with Nuitka..." -ForegroundColor Green
Write-Host "This will take 10-20 minutes on first build" -ForegroundColor Yellow
Write-Host ""

if ($Clean -and (Test-Path "dist")) {
    Write-Host "Cleaning old build..." -ForegroundColor Gray
    Remove-Item -Recurse -Force dist
}

Write-Host "Starting compilation..." -ForegroundColor Cyan
& .venv\Scripts\python.exe -m nuitka `
  --onefile `
  --follow-imports `
  --include-package=robo_rec `
  --include-package=bip_utils `
  --include-package=coincurve `
  --include-package=PySide6 `
  --windows-console-mode=disable `
  --output-dir=dist `
  src/robo_rec/main.py

if ($LASTEXITCODE -eq 0) {
    if (Test-Path "dist\main.exe") {
        $size = (Get-Item "dist\main.exe").Length / 1MB
        Write-Host ""
        Write-Host "✓ Build successful!" -ForegroundColor Green
        Write-Host "  Executable: dist\main.exe" -ForegroundColor Green
        Write-Host "  Size: $([math]::Round($size, 1)) MB" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "✗ Build completed but main.exe not found" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
