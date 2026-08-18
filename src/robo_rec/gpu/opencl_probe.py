"""Probes OpenCL GPU availability via seedrecover.py --opencl-info.

Confirmed on this dev machine (no discrete GPU, pyopencl not installed): btcrecover's
--opencl-info handler doesn't guard against pyopencl being unavailable and raises a bare
NameError (vendor/btcrecover/btcrecover/btcrseed.py line ~4877 calls opencl_information()
without checking the module_opencl_available flag set at import time, line ~81-88) instead of
printing a clean "not available" message. This is a real upstream bug, not something worth
patching here (unlike the --listseeds fix in robo-rec-implementation.md, this doesn't block a
PRD-required feature — it just means we must not assume a clean stderr on failure) — this
probe treats any non-zero exit or parse failure as "OpenCL unavailable" rather than raising.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from robo_rec.util.paths import btcrecover_root, seedrecover_script
from robo_rec.util.process import python_executable

_TIMEOUT_SECONDS = 15


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
    argv = [python_executable(), str(seedrecover_script()), "--opencl-info"]
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
        # e.g. pyopencl not installed, or no OpenCL platforms present on this machine. The
        # stderr is often a full Python traceback (confirmed on this dev machine — see
        # module docstring); only the last non-empty line is kept as a human-readable summary.
        stderr_lines = [ln for ln in completed.stderr.strip().splitlines() if ln.strip()]
        summary = stderr_lines[-1].strip() if stderr_lines else None
        return OpenClProbeResult(available=False, devices=[], error=summary)

    devices = _parse_devices(completed.stdout)
    return OpenClProbeResult(available=bool(devices), devices=devices, error=None)


def _parse_devices(output: str) -> list[OpenClDeviceInfo]:
    """Best-effort parse of opencl_information's printed device list. Format has not been
    observed on real hardware yet (no discrete GPU on the dev machine) — this must be
    re-verified against real --opencl-info output on the Windows VM / client hardware
    (see robo-rec-prd.md Section 6.3) and made more tolerant of format drift then."""
    devices: list[OpenClDeviceInfo] = []
    platform_id = -1
    device_id = -1
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("platform"):
            platform_id += 1
            device_id = -1
        elif stripped.lower().startswith("device") and ":" in stripped:
            device_id += 1
            name = stripped.split(":", 1)[1].strip()
            devices.append(
                OpenClDeviceInfo(platform_id=max(platform_id, 0), device_id=device_id, name=name)
            )
    return devices
