"""Probe basic CPU information using platform-native, dependency-free sources."""

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
    if platform.system() == "Windows":
        name = _windows_model_name_from_registry()
        if name:
            return name
    name = platform.processor()
    if name:
        return name
    if platform.system() == "Linux":
        return _linux_model_name_from_proc()
    return None


def _windows_model_name_from_registry() -> str | None:
    try:
        import winreg

        key_path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "ProcessorNameString")
    except (ImportError, OSError):
        return None
    return str(value).strip() or None


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
