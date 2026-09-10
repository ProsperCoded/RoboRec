"""Compose OpenCL, NVIDIA, optional PyCUDA, and CPU diagnostics into one report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from robo_rec.gpu import correctness_cache
from robo_rec.gpu.correctness_probe import probe_opencl_correctness, probe_opencl_device_signature
from robo_rec.gpu.cpu_probe import CpuInfo, probe_cpu
from robo_rec.gpu.nvidia_probe import probe_nvidia
from robo_rec.gpu.opencl_probe import OpenClDeviceInfo, probe_opencl
from robo_rec.gpu.pycuda_probe import probe_pycuda_importable
from robo_rec.util.paths import btcrecover_root


@dataclass(frozen=True)
class GpuStatusReport:
    opencl_available: bool
    opencl_devices: list[OpenClDeviceInfo]
    nvidia_gpu_name: str | None
    nvidia_driver_version: str | None
    cuda_toolkit_version: str | None
    pycuda_importable: bool
    cpu_info: CpuInfo
    probe_errors: list[str]
    generated_at: datetime
    # A GPU can be present and still produce wrong answers — confirmed directly on an
    # Intel NEO iGPU driver, whose PBKDF2 kernel silently skipped 7 of every 8
    # candidates. opencl_available says "a device exists"; opencl_usable says "it was
    # actually verified to compute correct results" (or is None if that was never
    # tested, e.g. no device was present to test in the first place).
    opencl_usable: bool | None = None
    opencl_usability_error: str | None = None
    opencl_usability_cached: bool = False
    opencl_usability_platform: str | None = None
    opencl_usability_device: str | None = None
    opencl_usability_driver: str | None = None

    @property
    def gpu_acceleration_available(self) -> bool:
        """Whether recovery will actually request GPU acceleration right now — presence
        AND a passed correctness check, not just presence (PRD 4.5's 'falls back
        cleanly to CPU' condition is the inverse of this)."""
        return self.opencl_available and bool(self.opencl_usable)

    @property
    def gpu_present_but_unusable(self) -> bool:
        """A GPU was detected but failed (or has never passed) the correctness check,
        so recovery uses CPU despite hardware being present — the state the top-bar
        badge and GPU Status panel must not silently collapse into either 'GPU
        Detected' (implies it's being used) or 'CPU Only' (hides that a GPU exists)."""
        return self.opencl_available and not bool(self.opencl_usable)


@dataclass(frozen=True)
class _GpuUsability:
    usable: bool | None = None
    error: str | None = None
    from_cache: bool = False
    platform_name: str | None = None
    device_name: str | None = None
    driver_version: str | None = None


def probe_gpu_status(
    *, btcrecover_dir: Path | None = None, force_recheck: bool = False
) -> GpuStatusReport:
    errors: list[str] = []
    btcrecover_dir = btcrecover_dir or btcrecover_root()

    opencl_result = probe_opencl()
    if opencl_result.error:
        errors.append(f"OpenCL: {opencl_result.error}")

    nvidia_result = probe_nvidia()
    if nvidia_result.error:
        errors.append(f"NVIDIA: {nvidia_result.error}")

    pycuda_ok = probe_pycuda_importable()
    # Recovery uses OpenCL, not PyCUDA.  Keep this informational field for
    # diagnostics without presenting an unused optional package as a failure.

    usability = _GpuUsability()
    if opencl_result.available:
        usability = _resolve_gpu_usability(btcrecover_dir, force_recheck=force_recheck)
        if usability.error and not usability.usable:
            errors.append(f"OpenCL correctness: {usability.error}")

    return GpuStatusReport(
        opencl_available=opencl_result.available,
        opencl_devices=opencl_result.devices,
        nvidia_gpu_name=nvidia_result.gpu_name,
        nvidia_driver_version=nvidia_result.driver_version,
        cuda_toolkit_version=nvidia_result.cuda_toolkit_version,
        pycuda_importable=pycuda_ok,
        cpu_info=probe_cpu(),
        probe_errors=errors,
        generated_at=datetime.now(UTC),
        opencl_usable=usability.usable,
        opencl_usability_error=usability.error,
        opencl_usability_cached=usability.from_cache,
        opencl_usability_platform=usability.platform_name,
        opencl_usability_device=usability.device_name,
        opencl_usability_driver=usability.driver_version,
    )


def _resolve_gpu_usability(btcrecover_dir: Path, *, force_recheck: bool) -> _GpuUsability:
    """Cheap identity probe first (no kernel compile — as fast as the presence check),
    so a cached verdict skips the expensive correctness probe entirely. Only runs
    the slow probe when this device/driver signature hasn't been tested before (or
    force_recheck asks to redo it) — see correctness_cache's module docstring for why
    the cache is keyed by device identity rather than by "does the file exist"."""
    identity = probe_opencl_device_signature(btcrecover_dir=btcrecover_dir)

    # A device/driver identity that couldn't be determined (e.g. the probe subprocess
    # itself failed to launch) has nothing to key a cache entry on — always test fresh
    # in that case rather than caching under a placeholder key.
    if not identity.platform_name or not identity.device_name:
        result = probe_opencl_correctness(btcrecover_dir=btcrecover_dir)
        return _GpuUsability(usable=result.usable, error=result.error or identity.error)

    signature = correctness_cache.device_signature(
        identity.platform_name, identity.device_name, identity.driver_version or ""
    )

    if force_recheck:
        correctness_cache.clear_verdict(signature)
    else:
        cached = correctness_cache.get_cached_verdict(signature)
        if cached is not None:
            return _GpuUsability(
                usable=cached.usable,
                error=cached.error,
                from_cache=True,
                platform_name=identity.platform_name,
                device_name=identity.device_name,
                driver_version=identity.driver_version,
            )

    result = probe_opencl_correctness(btcrecover_dir=btcrecover_dir)
    correctness_cache.store_verdict(signature, usable=result.usable, error=result.error)
    return _GpuUsability(
        usable=result.usable,
        error=result.error,
        platform_name=identity.platform_name,
        device_name=identity.device_name,
        driver_version=identity.driver_version,
    )


def export_json(report: GpuStatusReport, path: Path) -> None:
    payload = asdict(report)
    payload["generated_at"] = report.generated_at.isoformat()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
