"""Probe OpenCL GPU availability in an isolated subprocess.

Why not --opencl-info: btcrecover's own test suite (btcrecover/test/test_seeds.py's
has_any_opencl_devices(), which gates every OpenCL_Tests case) uses
btcrpass.get_opencl_devices() directly — not --opencl-info — as the canonical way to
detect a usable OpenCL setup. That function is a real, filtered device query
(pyopencl.get_platforms() -> get_devices(), keeping only devices where
d.available == 1, d.profile == "FULL_PROFILE", d.endian_little == 1) with its own
narrow exception handling: a missing pyopencl install is a caught ImportError, and
"no OpenCL platform found" is a caught pyopencl.LogicError — both return an empty
list cleanly. --opencl-info's own handler has no such guard (vendor/btcrecover/
btcrecover/btcrseed.py's opencl_information() call isn't gated by the
module_opencl_available flag set at import time) and raises a bare NameError when
pyopencl isn't installed, so scraping its stdout means treating a real upstream crash
as just another "empty output" case, and parsing device names/IDs out of
human-readable text whose exact format was never confirmed against real hardware.

The helper mirrors btcrpass.get_opencl_devices()'s filtering directly instead of
importing the vendored module. This matters in compiled builds: pyopencl is an
explicit build dependency, while the vendored btcrecover source tree is not an
importable Python package inside the one-file executable. The probe remains in a
subprocess so a driver crash during enumeration cannot take down the GUI process.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass

from robo_rec.util.paths import is_compiled
from robo_rec.util.process import python_executable

# Generous margin: this relaunches the whole executable as a subprocess just to run
# the probe helper, and on removable media an antivirus on-execute scan of that
# relaunch can itself take several seconds. A timeout that's too tight here reads
# as "GPU not available" even when the hardware and drivers are fine.
_TIMEOUT_SECONDS = 30
OPENCL_PROBE_HELPER_ARG = "--robo-rec-opencl-probe"

_DETECTION_SCRIPT = (
    "from robo_rec.gpu.opencl_probe import run_opencl_probe_helper; "
    "raise SystemExit(run_opencl_probe_helper())"
)


@dataclass(frozen=True)
class OpenClDeviceInfo:
    platform_id: int
    device_id: int
    name: str


@dataclass(frozen=True)
class OpenClProbeResult:
    available: bool
    devices: list[OpenClDeviceInfo]
    error: str | None


def probe_opencl() -> OpenClProbeResult:
    # A compiled Nuitka executable is not a general-purpose Python interpreter,
    # so ``main.exe -c ...`` cannot run the helper script.  Re-enter the app in
    # a dedicated helper mode instead.  Source runs continue to use the active
    # virtual environment's interpreter.
    argv = (
        [sys.executable, OPENCL_PROBE_HELPER_ARG]
        if is_compiled()
        else [python_executable(), "-c", _DETECTION_SCRIPT]
    )
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return OpenClProbeResult(available=False, devices=[], error=str(exc))

    if completed.returncode != 0:
        stderr_lines = [ln for ln in completed.stderr.strip().splitlines() if ln.strip()]
        summary = stderr_lines[-1].strip() if stderr_lines else f"exit code {completed.returncode}"
        return OpenClProbeResult(available=False, devices=[], error=summary)

    return _parse_result(completed.stdout)


def run_opencl_probe_helper() -> int:
    """Entry point used by the compiled executable's OpenCL helper mode."""
    try:
        import pyopencl
        from numpy import __version__ as numpy_version
    except ImportError as exc:
        print(json.dumps({"ok": False, "error": f"Missing OpenCL dependency: {exc}"}))
        return 0
    except OSError as exc:
        # pyopencl's own __init__.py raises OSError (not ImportError) if it can't
        # locate its bundled "cl/" include directory next to itself — a packaging
        # gap (missing data files), not a missing-dependency one, but just as fatal
        # to importing the module.
        print(json.dumps({"ok": False, "error": f"pyopencl failed to load: {exc}"}))
        return 0

    # Reference the imports so static packagers include both extension packages.
    _ = numpy_version

    try:
        devices = []
        for platform in pyopencl.get_platforms():
            for device in platform.get_devices():
                if (
                    device.available == 1
                    and device.profile == "FULL_PROFILE"
                    and device.endian_little == 1
                ):
                    devices.append(device)
    except pyopencl.LogicError as exc:
        # Match btcrecover's clean no-platform fallback while preserving
        # unexpected driver/API failures as diagnostics.
        if "platform not found" in str(exc).lower():
            devices = []
        else:
            print(json.dumps({"ok": False, "error": f"LogicError: {exc}"}))
            return 0
    except Exception as exc:  # noqa: BLE001 - isolate arbitrary OpenCL driver failures
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 0

    result = []
    for index, device in enumerate(devices):
        try:
            platform_name = device.platform.name
        except Exception:  # noqa: BLE001 - optional driver metadata can fail independently
            platform_name = "unknown"
        result.append({"platform": platform_name, "index": index, "name": device.name})

    print(json.dumps({"ok": True, "devices": result}))
    return 0


def _parse_result(stdout: str) -> OpenClProbeResult:
    # Scan from the end for a line that parses as our JSON payload shape, rather than
    # assuming the very last line always is one. Some OpenCL ICD drivers print stray
    # warnings to stdout (not stderr) around enumeration, which would otherwise land
    # after our JSON line and make a perfectly good result look like "no output."
    payload = None
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "ok" in candidate:
            payload = candidate
            break

    if not payload:
        return OpenClProbeResult(available=False, devices=[], error="No output from OpenCL probe script")

    if not payload.get("ok"):
        return OpenClProbeResult(available=False, devices=[], error=payload.get("error"))

    # get_opencl_devices() returns a flat list across all platforms (pyopencl.Device
    # has no numeric platform id, only a name) — derive platform_id here by first
    # appearance order, so devices on the same platform share an id without
    # fabricating one.
    platform_ids: dict[str, int] = {}
    devices: list[OpenClDeviceInfo] = []
    for entry in payload.get("devices", []):
        platform_name = entry.get("platform", "")
        platform_id = platform_ids.setdefault(platform_name, len(platform_ids))
        devices.append(
            OpenClDeviceInfo(
                platform_id=platform_id,
                device_id=entry.get("index", 0),
                name=entry.get("name", "Unknown device"),
            )
        )
    return OpenClProbeResult(available=bool(devices), devices=devices, error=None)


__all__ = [
    "OPENCL_PROBE_HELPER_ARG",
    "OpenClDeviceInfo",
    "OpenClProbeResult",
    "probe_opencl",
    "run_opencl_probe_helper",
]
