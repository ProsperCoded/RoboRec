"""Probes basic CPU info for display when no GPU acceleration is available (PRD 4.5's
'falls back cleanly to CPU' — this gives the user something concrete to look at instead of
just "no GPU"). Pure stdlib, no subprocess.

platform.processor() is unreliable on Linux (returns '' — a known stdlib gap; it works on
Windows, which is the shipping target per the PRD) so the model name is read from
/proc/cpuinfo on Linux as a fallback, purely for local dev-machine testing/display.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CpuInfo:
    model_name: str | None
    architecture: str
    logical_cores: int | None
    os_name: str


def probe_cpu() -> CpuInfo:
    return CpuInfo(
        model_name=_model_name(),
        architecture=platform.machine() or "unknown",
        logical_cores=_logical_cores(),
        os_name=f"{platform.system()} {platform.release()}".strip(),
    )


def _model_name() -> str | None:
    name = platform.processor()
    if name:
        return name
    if platform.system() == "Linux":
        return _linux_model_name_from_proc()
    return None


def _linux_model_name_from_proc() -> str | None:
    try:
        text = Path("/proc/cpuinfo").read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("model name"):
            _, _, value = line.partition(":")
            return value.strip() or None
    return None


def _logical_cores() -> int | None:
    return os.cpu_count()
