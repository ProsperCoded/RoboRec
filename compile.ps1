# Build RoboRec with Nuitka as a standalone folder (Roborec.dist\Roborec.exe)
param(
    [switch]$Clean = $true
)

$ErrorActionPreference = "Stop"

$REPO_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $REPO_ROOT

Write-Host "Building RoboRec with Nuitka..." -ForegroundColor Green
Write-Host "This will take 10-20 minutes on first build" -ForegroundColor Yellow
Write-Host ""

if ($Clean -and (Test-Path "dist")) {
    Write-Host "Cleaning old build..." -ForegroundColor Gray
    Remove-Item -Recurse -Force dist
}

$numCores = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
Write-Host "Starting compilation on $numCores cores..." -ForegroundColor Cyan
$nuitkaArgs = @(
    "-m"
    "nuitka"
    "--standalone"
    "--follow-imports"
    "--enable-plugin=pyside6"
    "--include-package=robo_rec"
    "--include-package=bip_utils"
    "--include-package=coincurve"
    "--include-package=PySide6"
    "--include-package=Crypto"
    "--include-package=py_crypto_hd_wallet"
    "--include-package=numpy"
    "--include-package=pyopencl"
    "--include-data-dir=src/robo_rec/gui/assets=robo_rec/gui/assets"
    "--include-data-dir=vendor=vendor"
    "--windows-icon-from-ico=src/robo_rec/gui/assets/app-icon.ico"
    "--windows-console-mode=disable"
    "--output-filename=Roborec.exe"
    "--jobs=$numCores"
    "--lto=auto"
    "--output-dir=dist"
    "src/robo_rec/main.py"
)

& .venv\Scripts\python.exe @nuitkaArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

$exe = Get-ChildItem -Path dist -Recurse -Filter "Roborec.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $exe) {
    Write-Host "Build completed but Roborec.exe not found under dist\" -ForegroundColor Red
    exit 1
}
$appFolder = $exe.Directory.FullName

# --- Stage 2: compile vendor/btcrecover/seedrecover.py into its own executable. ---
# Roborec.exe never runs recovery itself — it shells out to seedrecover.exe (see
# robo_rec.util.paths.seedrecover_command()) and streams its output. Nothing built that
# executable before, which is exactly the "[WinError 2] The system cannot find the file
# specified" failure when clicking Proceed: repo_root()/seedrecover.exe was expected but
# never produced. This stage builds it and merges it into the same app folder as
# Roborec.exe, matching what seedrecover_command() looks for.
Write-Host ""
Write-Host "Building seedrecover.exe (recovery engine) with Nuitka..." -ForegroundColor Green

$seedrecoverBuildDir = Join-Path $REPO_ROOT "dist\_seedrecover_build"
Push-Location (Join-Path $REPO_ROOT "vendor\btcrecover")
try {
    $seedrecoverArgs = @(
        "-m"
        "nuitka"
        "--standalone"
        "--follow-imports"
        "--include-package=btcrecover"
        "--include-package=lib"
        "--include-package=bip_utils"
        "--include-package=coincurve"
        "--include-package=Crypto"
        "--include-package=py_crypto_hd_wallet"
        "--include-package=numpy"
        "--include-package=pyopencl"
        "--include-package=google.protobuf"
        "--include-data-dir=btcrecover/wordlists=btcrecover/wordlists"
        "--include-data-dir=btcrecover/opencl=btcrecover/opencl"
        "--output-filename=seedrecover.exe"
        "--jobs=$numCores"
        "--lto=auto"
        "--output-dir=$seedrecoverBuildDir"
        "seedrecover.py"
    )
    & "$REPO_ROOT\.venv\Scripts\python.exe" @seedrecoverArgs
    $seedrecoverExit = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($seedrecoverExit -ne 0) {
    Write-Host "seedrecover.exe build failed with exit code $seedrecoverExit" -ForegroundColor Red
    Write-Host "Roborec.exe built fine, but recovery will fail with WinError 2 until this is fixed." -ForegroundColor Yellow
    exit $seedrecoverExit
}

$seedrecoverExe = Get-ChildItem -Path $seedrecoverBuildDir -Recurse -Filter "seedrecover.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $seedrecoverExe) {
    Write-Host "seedrecover build completed but seedrecover.exe not found under $seedrecoverBuildDir" -ForegroundColor Red
    exit 1
}

Write-Host "Merging seedrecover.exe and its dependencies into the app folder..." -ForegroundColor Cyan
Copy-Item -Path (Join-Path $seedrecoverExe.Directory.FullName "*") -Destination $appFolder -Recurse -Force

$mergedSeedrecover = Join-Path $appFolder "seedrecover.exe"
if (-not (Test-Path $mergedSeedrecover)) {
    Write-Host "Merge completed but seedrecover.exe is missing from $appFolder" -ForegroundColor Red
    exit 1
}

$folderSize = (Get-ChildItem -Path $appFolder -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host ""
Write-Host "Build successful!" -ForegroundColor Green
Write-Host "  Folder to copy:  $appFolder" -ForegroundColor Green
Write-Host "  Main executable: $($exe.FullName)" -ForegroundColor Green
Write-Host "  Recovery engine: $mergedSeedrecover" -ForegroundColor Green
Write-Host "  Total size: $([math]::Round($folderSize, 1)) MB" -ForegroundColor Green
Write-Host ""
Write-Host "Copy the WHOLE folder above to the flash drive, not just the .exe." -ForegroundColor Yellow
exit 0
