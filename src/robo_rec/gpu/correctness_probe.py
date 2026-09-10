"""Launches vendor/btcrecover's OpenCL correctness self-test in a subprocess.

Presence of an OpenCL device (robo_rec.gpu.opencl_probe) says nothing about whether the
driver computes correct results — confirmed by direct testing on an Intel NEO iGPU
driver: the generic pbkdf2 kernel silently returned all-zero digests for 7 of every 8
candidates, with no error, which made real recovery searches report "Seed not found"
even when the correct phrase was in range. This probe answers the only question that
actually matters for recovery: not "is a GPU present" but "does it produce correct
answers."

Routed through seedrecover.exe (via the same --robo-rec-opencl-correctness-probe
sentinel arg added to vendor/btcrecover/seedrecover.py), not Roborec.exe, deliberately:
seedrecover.exe's own Nuitka build already compiles in lib.opencl_brute (it's what
real recovery runs through), so this reuses an already-proven import path instead of
gambling on Roborec.exe dynamically importing vendor .py files it never bundled as
frozen code. See vendor/btcrecover/robo_rec_opencl_correctness.py for the probe itself.

Kept in a subprocess for the same reason robo_rec.gpu.opencl_probe is: a GPU driver
crash during kernel compilation/execution must not be able to take down the GUI.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from robo_rec.util.paths import btcrecover_root, seedrecover_command

# The identity probe is pure pyopencl device enumeration (no kernel compile), so it's
# as cheap as robo_rec.gpu.opencl_probe's presence check and shares its timeout/margin
# reasoning: a relaunch on removable media can cost several seconds to an on-execute
# antivirus scan alone, independent of the actual work being probed.
_IDENTITY_TIMEOUT_SECONDS = 30
# The full probe additionally compiles and runs a real OpenCL kernel (observed at a
# few seconds on working hardware) — generous margin on top of the above.
_CORRECTNESS_TIMEOUT_SECONDS = 60

DEVICE_SIGNATURE_ARG = "--robo-rec-opencl-device-signature"
CORRECTNESS_PROBE_ARG = "--robo-rec-opencl-correctness-probe"


@dataclass(frozen=True)
class DeviceIdentityResult:
    platform_name: str | None
    device_name: str | None
    driver_version: str | None
    error: str | None


@dataclass(frozen=True)
class OpenClCorrectnessResult:
    usable: bool
    platform_name: str | None
    device_name: str | None
    driver_version: str | None
    error: str | None


def probe_opencl_device_signature(*, btcrecover_dir: Path | None = None) -> DeviceIdentityResult:
    """Cheap: which OpenCL device would recovery auto-select, with no kernel compile.
    Callers use this to look up a cached correctness verdict before ever paying for
    the expensive probe_opencl_correctness() below."""
    payload = _run_probe(
        DEVICE_SIGNATURE_ARG, btcrecover_dir=btcrecover_dir, timeout=_IDENTITY_TIMEOUT_SECONDS
    )
    if payload is None or not payload.get("ok"):
        error = (
            "No output from OpenCL device-signature probe"
            if payload is None
            else payload.get("error", "Unknown device-signature probe failure")
        )
        return DeviceIdentityResult(None, None, None, error)
    return DeviceIdentityResult(
        platform_name=payload.get("platform_name"),
        device_name=payload.get("device_name"),
        driver_version=payload.get("driver_version"),
        error=None,
    )


def probe_opencl_correctness(*, btcrecover_dir: Path | None = None) -> OpenClCorrectnessResult:
    payload = _run_probe(
        CORRECTNESS_PROBE_ARG,
        btcrecover_dir=btcrecover_dir,
        timeout=_CORRECTNESS_TIMEOUT_SECONDS,
    )
    if payload is None or not payload.get("ok"):
        error = (
            "No output from OpenCL correctness probe"
            if payload is None
            else payload.get("error", "Unknown correctness-probe failure")
        )
        return OpenClCorrectnessResult(False, None, None, None, error)
    return OpenClCorrectnessResult(
        usable=bool(payload.get("usable", False)),
        platform_name=payload.get("platform_name"),
        device_name=payload.get("device_name"),
        driver_version=payload.get("driver_version"),
        error=payload.get("error"),
    )


def _run_probe(sentinel_arg: str, *, btcrecover_dir: Path | None, timeout: int) -> dict | None:
    """Launches seedrecover with the given sentinel arg and returns its parsed JSON
    payload, or None if nothing parseable came back (launch failure, timeout, crash
    before the probe could print anything)."""
    argv = [*seedrecover_command(), sentinel_arg]
    cwd = btcrecover_dir or btcrecover_root()
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": f"Failed to launch probe: {exc}"}

    # Scan from the end for a line that parses as our JSON payload shape, mirroring
    # opencl_probe._parse_result: some OpenCL ICD drivers print stray compiler/JIT
    # warnings to stdout around kernel builds (observed directly — Intel's NEO driver's
    # "RetryManager" recompilation notices), which would otherwise land after our JSON
    # line and make a perfectly good result look like "no output."
    for line in reversed(completed.stdout.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "ok" in candidate:
            return candidate
    return None


__all__ = [
    "CORRECTNESS_PROBE_ARG",
    "DEVICE_SIGNATURE_ARG",
    "DeviceIdentityResult",
    "OpenClCorrectnessResult",
    "probe_opencl_correctness",
    "probe_opencl_device_signature",
]
