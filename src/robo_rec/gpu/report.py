"""Composes the OpenCL, NVIDIA driver, PyCUDA, and CPU probes into one status report
(PRD 4.5).

Every GPU probe's failure is caught and appended to probe_errors rather than raised — this
dev machine has no discrete GPU, so every code path here must degrade gracefully; that's also
exactly what makes it fully testable right now (mocked subprocess output covers the "no GPU"
branch, which is this machine's actual live state). CPU info is always populated (it's pure
stdlib, no failure mode) so the GPU Status view has something concrete to show when no GPU is
detected, rather than just an absence.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from robo_rec.gpu.cpu_probe import CpuInfo, probe_cpu
from robo_rec.gpu.nvidia_probe import probe_nvidia
from robo_rec.gpu.opencl_probe import OpenClDeviceInfo, probe_opencl
from robo_rec.gpu.pycuda_probe import probe_pycuda_importable


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

    @property
    def gpu_acceleration_available(self) -> bool:
        """Whether recovery can actually use GPU acceleration right now (PRD 4.5's
        'falls back cleanly to CPU' condition is the inverse of this)."""
        return self.opencl_available


def probe_gpu_status(*, btcrecover_dir: Path | None = None) -> GpuStatusReport:
    errors: list[str] = []

    opencl_result = probe_opencl()
    if opencl_result.error:
        errors.append(f"OpenCL: {opencl_result.error}")

    nvidia_result = probe_nvidia()
    if nvidia_result.error:
        errors.append(f"NVIDIA: {nvidia_result.error}")

    pycuda_ok = probe_pycuda_importable()
    if not pycuda_ok:
        errors.append("PyCUDA: module not importable")

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
    )


def export_json(report: GpuStatusReport, path: Path) -> None:
    payload = asdict(report)
    payload["generated_at"] = report.generated_at.isoformat()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
