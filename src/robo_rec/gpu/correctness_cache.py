"""Persistent cache of GPU OpenCL correctness-test verdicts, keyed by device signature.

Running the actual correctness probe (compile a kernel, run known PBKDF2 vectors
through it, compare against hashlib) costs real time — a kernel compile plus subprocess
relaunch, observed at several seconds even on working hardware. Re-running it on every
app launch would make every startup pay that cost. This cache makes it a one-time cost
per device/driver combination instead: slow the first time a given GPU is seen, free
thereafter.

Keyed by device signature (platform name + device name + driver version), not just
"does the cache file exist" — RoboRec is explicitly designed to be copied whole onto a
flash drive and run on different machines (see compile.ps1's own "Copy the WHOLE folder
to the flash drive" instruction). A flat present/absent cache would silently reuse one
machine's verdict on a different machine's GPU, or keep an old verdict after a driver
update changes correctness. Keying by signature means the file can safely travel with
the drive: a machine/GPU/driver combination it has already tested is fast, and a new
one gets tested fresh and recorded alongside whatever's already there.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from robo_rec.util.paths import repo_root

_CACHE_FILENAME = "gpu_config.json"


@dataclass(frozen=True)
class CorrectnessVerdict:
    usable: bool
    error: str | None
    tested_at: str  # ISO 8601; kept as str so this round-trips through JSON unchanged


def default_cache_path() -> Path:
    return repo_root() / _CACHE_FILENAME


def device_signature(platform_name: str, device_name: str, driver_version: str) -> str:
    """One string identifying a specific GPU/driver combination well enough to know
    whether a past correctness verdict still applies. A driver update changing
    driver_version is exactly the kind of change that should trigger a fresh test."""
    return f"{platform_name.strip()}|{device_name.strip()}|{driver_version.strip()}"


def _load_all(cache_path: Path) -> dict[str, dict]:
    try:
        raw = cache_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # A corrupted cache file must never crash startup or permanently wedge the app
        # into skipping the (self-correcting) correctness test — treat it as empty and
        # let the next store_verdict() naturally repair the file on disk.
        return {}
    devices = data.get("devices") if isinstance(data, dict) else None
    return devices if isinstance(devices, dict) else {}


def _save_all(cache_path: Path, devices: dict[str, dict]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: a crash or antivirus scan mid-write must never leave a half-written,
    # unparseable JSON file that then permanently fails every future load.
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=".gpu_config-", suffix=".tmp", dir=str(cache_path.parent)
    )
    tmp_path = Path(tmp_path_str)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump({"devices": devices}, f, indent=2)
        os.replace(tmp_path, cache_path)
    except BaseException:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def get_cached_verdict(
    signature: str, *, cache_path: Path | None = None
) -> CorrectnessVerdict | None:
    path = cache_path or default_cache_path()
    entry = _load_all(path).get(signature)
    if not isinstance(entry, dict) or "usable" not in entry:
        return None
    return CorrectnessVerdict(
        usable=bool(entry["usable"]),
        error=entry.get("error"),
        tested_at=entry.get("tested_at", ""),
    )


def store_verdict(
    signature: str, *, usable: bool, error: str | None, cache_path: Path | None = None
) -> None:
    path = cache_path or default_cache_path()
    devices = _load_all(path)
    devices[signature] = {
        "usable": usable,
        "error": error,
        "tested_at": datetime.now(UTC).isoformat(),
    }
    _save_all(path, devices)


def clear_verdict(signature: str, *, cache_path: Path | None = None) -> None:
    """Removes only this device's cached entry, not the whole file — a portable
    flash-drive cache holding verdicts for several machines shouldn't be wiped by
    re-checking on just one of them (the GUI's "Re-check GPU" button)."""
    path = cache_path or default_cache_path()
    devices = _load_all(path)
    if signature in devices:
        del devices[signature]
        _save_all(path, devices)


__all__ = [
    "CorrectnessVerdict",
    "clear_verdict",
    "default_cache_path",
    "device_signature",
    "get_cached_verdict",
    "store_verdict",
]
