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
  --standalone ^
  --follow-imports ^
  --enable-plugin=pyside6 ^
  --include-package=robo_rec ^
  --include-package=bip_utils ^
  --include-package=coincurve ^
  --include-package=PySide6 ^
  --include-package=Crypto ^
  --include-package=py_crypto_hd_wallet ^
  --include-package=numpy ^
  --include-package=pyopencl ^
  --include-data-dir="src/robo_rec/gui/assets=robo_rec/gui/assets" ^
  --include-data-dir="vendor=vendor" ^
  --windows-icon-from-ico="src/robo_rec/gui/assets/app-icon.ico" ^
  --windows-console-mode=disable ^
  --output-filename=Roborec.exe ^
  --jobs=%NUM_CORES% ^
  --lto=auto ^
  --output-dir=dist ^
  src/robo_rec/main.py

if %errorlevel% equ 0 (
    set "EXEPATH="
    for /f "delims=" %%F in ('dir /s /b dist\Roborec.exe 2^>nul') do set "EXEPATH=%%F"
    if defined EXEPATH (
        for %%F in ("!EXEPATH!") do set "EXEDIR=%%~dpF"
        for /F "usebackq" %%A in ('powershell -Command "(Get-ChildItem -Path '!EXEDIR!' -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB | ForEach-Object { [Math]::Round($_, 1) }"') do set SIZE=%%A
        echo.
        echo ✓ Build successful!
        echo   Folder to copy: !EXEDIR!
        echo   Executable:     !EXEPATH!
        echo   Total size:     !SIZE! MB
        echo.
        echo Copy the WHOLE folder above to the flash drive, not just the .exe.
        exit /b 0
    ) else (
        echo ✗ Build completed but Roborec.exe not found under dist\
        exit /b 1
    )
) else (
    echo ✗ Build failed with exit code %errorlevel%
    exit /b %errorlevel%
)
