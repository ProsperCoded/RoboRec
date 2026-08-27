"""Probes OpenCL GPU availability by calling btcrecover's own detection function,
btcrpass.get_opencl_devices(), instead of parsing seedrecover.py --opencl-info's
human-readable text output.

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

This probe instead runs a small script that imports btcrpass (the same module
seedrecover.py itself already imports for every real run, so this carries no
additional import risk) and calls get_opencl_devices() directly, printing the result
as JSON. It's still run in a subprocess — not imported in-process — so a pyopencl
driver crash during device enumeration can't take down the GUI process itself.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass

from robo_rec.util.paths import btcrecover_root

_TIMEOUT_SECONDS = 15

# Run from btcrecover_root as cwd (matches how seedrecover.py itself is always
# launched elsewhere in this codebase — see util/paths.py), so
# `from btcrecover import btcrpass` resolves the same way it does for a real
# recovery run (seedrecover.py itself does `from btcrecover import btcrseed`).
_DETECTION_SCRIPT = """
import json, sys
try:
    from btcrecover import btcrpass
except Exception as exc:
    print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
    sys.exit(0)

try:
    devices = btcrpass.get_opencl_devices()
except Exception as exc:
    print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
    sys.exit(0)

result = []
for i, d in enumerate(devices):
    try:
        platform_name = d.platform.name
    except Exception:
        platform_name = "unknown"
    result.append({"platform": platform_name, "index": i, "name": d.name})
print(json.dumps({"ok": True, "devices": result}))
"""


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
    argv = [sys.executable, "-c", _DETECTION_SCRIPT]
    try:
        completed = subprocess.run(
            argv,
            cwd=str(btcrecover_root()),
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


def _parse_result(stdout: str) -> OpenClProbeResult:
    try:
        payload = json.loads(stdout.strip().splitlines()[-1]) if stdout.strip() else None
    except (json.JSONDecodeError, IndexError):
        payload = None

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


__all__ = ["OpenClDeviceInfo", "OpenClProbeResult", "probe_opencl"]
