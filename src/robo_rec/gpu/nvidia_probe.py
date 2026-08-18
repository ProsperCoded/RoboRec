"""Probes NVIDIA driver / CUDA toolkit presence via nvidia-smi (PRD 4.5).

Confirmed on this dev machine: nvidia-smi is simply absent (no discrete NVIDIA GPU, per PRD
6.1). shutil.which() gates every call so we never spawn a doomed subprocess. Output format
must be re-verified against a real NVIDIA driver on the Windows VM / client hardware (PRD
6.3) — this parser stays deliberately defensive/tolerant.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class NvidiaProbeResult:
    driver_version: str | None
    cuda_toolkit_version: str | None
    gpu_name: str | None
    error: str | None


def probe_nvidia() -> NvidiaProbeResult:
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return NvidiaProbeResult(
            driver_version=None,
            cuda_toolkit_version=None,
            gpu_name=None,
            error="nvidia-smi not found on PATH (no NVIDIA driver installed, or no NVIDIA GPU present)",
        )

    driver_version, gpu_name, query_error = _query_driver_and_name(nvidia_smi)
    cuda_version = _query_cuda_version(nvidia_smi)
    return NvidiaProbeResult(
        driver_version=driver_version,
        cuda_toolkit_version=cuda_version,
        gpu_name=gpu_name,
        error=query_error,
    )


def _query_driver_and_name(nvidia_smi: str) -> tuple[str | None, str | None, str | None]:
    try:
        completed = subprocess.run(
            [nvidia_smi, "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, None, str(exc)

    if completed.returncode != 0:
        return None, None, completed.stderr.strip() or "nvidia-smi query failed"

    first_line = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else ""
    if "," not in first_line:
        return None, None, f"Unexpected nvidia-smi output: {first_line!r}"
    name, driver_version = (part.strip() for part in first_line.split(",", 1))
    return driver_version, name, None


def _query_cuda_version(nvidia_smi: str) -> str | None:
    """nvidia-smi's plain (non --query) header includes a 'CUDA Version: X.Y' field this
    driver supports; there's no dedicated --query-gpu field for it as of typical nvidia-smi
    versions, so this parses the header text."""
    try:
        completed = subprocess.run(
            [nvidia_smi], capture_output=True, text=True, timeout=_TIMEOUT_SECONDS, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    for line in completed.stdout.splitlines():
        if "CUDA Version" in line:
            marker = "CUDA Version:"
            idx = line.find(marker)
            if idx != -1:
                remainder = line[idx + len(marker):].strip()
                return remainder.split()[0] if remainder else None
    return None
