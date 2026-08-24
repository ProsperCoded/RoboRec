@echo off
setlocal enabledelayedexpansion

echo Cleaning up previous builds...
if exist dist rmdir /s /q dist
if exist main.exe del /q main.exe
if exist seedrecover.exe del /q seedrecover.exe

echo Compiling Robo-Rec with Nuitka...
uv run python -m nuitka ^
  --onefile ^
  --windows-console-mode=disable ^
  --enable-plugin=pyside6 ^
  --main=src/robo_rec/main.py ^
  --main=vendor/btcrecover/seedrecover.py ^
  --include-data-dir=vendor/btcrecover/derivationpath-lists=vendor/btcrecover/derivationpath-lists ^
  --include-data-dir=vendor/btcrecover/btcrecover/wordlists=btcrecover/wordlists ^
  --include-data-dir=vendor/btcrecover/btcrecover/wordlists=vendor/btcrecover/wordlists ^
  --output-dir=dist

if %ERRORLEVEL% neq 0 (
    echo Compilation failed!
    pause
    exit /b %ERRORLEVEL%
)

echo Done! The compiled executables (main.exe and seedrecover.exe) are in the dist\ folder.
pause
