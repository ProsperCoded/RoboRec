@echo off
REM Build RoboRec with Nuitka into a single Windows executable
setlocal enabledelayedexpansion

set "REPO_ROOT=%~dp0"
cd /d "%REPO_ROOT%"

echo.
echo 🔨 Building RoboRec with Nuitka...
echo This will take 10-20 minutes on first build
echo.

if exist dist (
    echo Cleaning old build...
    rmdir /s /q dist
)

for /f %%A in ('powershell -Command "(Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors"') do set NUM_CORES=%%A
echo Starting compilation on %NUM_CORES% cores...
call .venv\Scripts\python.exe -m nuitka ^
  --onefile ^
  --follow-imports ^
  --enable-plugin=pyside6 ^
  --include-package=robo_rec ^
  --include-package=bip_utils ^
  --include-package=coincurve ^
  --include-package=PySide6 ^
  --include-package=Crypto ^
  --include-package=py_crypto_hd_wallet ^
  --include-data-dir="src/robo_rec/gui/assets=robo_rec/gui/assets" ^
  --include-data-dir="vendor=vendor" ^
  --windows-console-mode=disable ^
  --jobs=%NUM_CORES% ^
  --lto=auto ^
  --output-dir=dist ^
  src/robo_rec/main.py

if %errorlevel% equ 0 (
    if exist dist\main.exe (
        for /F "usebackq" %%A in ('powershell -Command "(Get-Item dist\main.exe).Length / 1MB | ForEach-Object { [Math]::Round($_, 1) }"') do set SIZE=%%A
        echo.
        echo ✓ Build successful!
        echo   Executable: dist\main.exe
        echo   Size: !SIZE! MB
        exit /b 0
    ) else (
        echo ✗ Build completed but main.exe not found
        exit /b 1
    )
) else (
    echo ✗ Build failed with exit code %errorlevel%
    exit /b %errorlevel%
)
