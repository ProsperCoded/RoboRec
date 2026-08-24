# Clean up previous build directories
Write-Host "Cleaning up previous builds..." -ForegroundColor Cyan
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path main.exe) { Remove-Item -Force main.exe }
if (Test-Path seedrecover.exe) { Remove-Item -Force seedrecover.exe }

Write-Host "Compiling Robo-Rec with Nuitka..." -ForegroundColor Cyan
uv run python -m nuitka `
  --onefile `
  --windows-console-mode=disable `
  --enable-plugin=pyside6 `
  --main=src/robo_rec/main.py `
  --main=vendor/btcrecover/seedrecover.py `
  --include-data-dir=vendor/btcrecover/derivationpath-lists=vendor/btcrecover/derivationpath-lists `
  --include-data-dir=vendor/btcrecover/btcrecover/wordlists=btcrecover/wordlists `
  --include-data-dir=vendor/btcrecover/btcrecover/wordlists=vendor/btcrecover/wordlists `
  --output-dir=dist

if ($LASTEXITCODE -eq 0) {
    Write-Host "Done! The compiled executables (main.exe and seedrecover.exe) are in the dist/ folder." -ForegroundColor Green
} else {
    Write-Host "Compilation failed!" -ForegroundColor Red
}
