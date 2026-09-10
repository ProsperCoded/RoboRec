"""Tests for the GPU OpenCL correctness cache and its wiring into probe_gpu_status().

Presence of an OpenCL device says nothing about whether it computes correct results —
confirmed directly on an Intel NEO iGPU driver whose PBKDF2 kernel silently returned
wrong digests for 7 of every 8 candidates with no error at all. These tests cover the
cache that makes verifying this a one-time cost per device/driver combination, and the
tri-state (usable / present-but-unusable / absent) reporting built on top of it.
"""

from __future__ import annotations

from unittest.mock import patch

from robo_rec.gpu import correctness_cache as cache
from robo_rec.gpu.correctness_probe import DeviceIdentityResult, OpenClCorrectnessResult
from robo_rec.gpu.opencl_probe import OpenClDeviceInfo, OpenClProbeResult
from robo_rec.gpu.report import probe_gpu_status

_SIG = cache.device_signature("Test Platform", "Test Device", "1.2.3")


def test_device_signature_is_stable_and_trims_whitespace():
    a = cache.device_signature("Plat ", " Dev", "1.0 ")
    b = cache.device_signature("Plat", "Dev", "1.0")
    assert a == b


def test_cache_roundtrip(tmp_path):
    path = tmp_path / "gpu_config.json"
    assert cache.get_cached_verdict(_SIG, cache_path=path) is None

    cache.store_verdict(_SIG, usable=True, error=None, cache_path=path)
    verdict = cache.get_cached_verdict(_SIG, cache_path=path)
    assert verdict is not None
    assert verdict.usable is True
    assert verdict.error is None
    assert verdict.tested_at  # populated, ISO-ish timestamp


def test_cache_clear_removes_only_the_given_device(tmp_path):
    """A portable, flash-drive cache may hold verdicts for several machines — clearing
    one device's entry (the GPU Status panel's Re-check button) must not wipe the
    others."""
    path = tmp_path / "gpu_config.json"
    other_sig = cache.device_signature("Other Platform", "Other Device", "9.9.9")
    cache.store_verdict(_SIG, usable=False, error="broken", cache_path=path)
    cache.store_verdict(other_sig, usable=True, error=None, cache_path=path)

    cache.clear_verdict(_SIG, cache_path=path)

    assert cache.get_cached_verdict(_SIG, cache_path=path) is None
    assert cache.get_cached_verdict(other_sig, cache_path=path) is not None


def test_cache_survives_corrupted_file(tmp_path):
    path = tmp_path / "gpu_config.json"
    path.write_text("not valid json {{{", encoding="utf-8")
    assert cache.get_cached_verdict(_SIG, cache_path=path) is None
    # And writing after corruption repairs the file rather than erroring.
    cache.store_verdict(_SIG, usable=True, error=None, cache_path=path)
    assert cache.get_cached_verdict(_SIG, cache_path=path).usable is True


def test_cache_missing_file_is_not_an_error(tmp_path):
    path = tmp_path / "does-not-exist" / "gpu_config.json"
    assert cache.get_cached_verdict(_SIG, cache_path=path) is None


def _opencl_available(name="Test Device"):
    return OpenClProbeResult(
        available=True,
        devices=[OpenClDeviceInfo(platform_id=0, device_id=0, name=name)],
        error=None,
    )


def _identity_ok():
    return DeviceIdentityResult("Test Platform", "Test Device", "1.2.3", None)


def _identity_missing():
    return DeviceIdentityResult(None, None, None, "no device")


def test_report_no_gpu_never_calls_correctness_probe():
    """Nothing to test when there's no OpenCL device at all — the (expensive)
    correctness probe must never even be attempted."""
    with (
        patch(
            "robo_rec.gpu.report.probe_opencl",
            return_value=OpenClProbeResult(available=False, devices=[], error=None),
        ),
        patch("robo_rec.gpu.report.probe_opencl_device_signature") as sig_mock,
        patch("robo_rec.gpu.report.probe_opencl_correctness") as full_mock,
    ):
        report = probe_gpu_status()

    sig_mock.assert_not_called()
    full_mock.assert_not_called()
    assert report.opencl_usable is None
    assert report.gpu_acceleration_available is False
    assert report.gpu_present_but_unusable is False


def test_report_uncached_device_runs_full_probe_and_stores_verdict(tmp_path):
    cache_path = tmp_path / "gpu_config.json"
    with (
        patch("robo_rec.gpu.report.probe_opencl", return_value=_opencl_available()),
        patch("robo_rec.gpu.report.probe_opencl_device_signature", return_value=_identity_ok()),
        patch(
            "robo_rec.gpu.report.probe_opencl_correctness",
            return_value=OpenClCorrectnessResult(
                usable=False,
                platform_name="Test Platform",
                device_name="Test Device",
                driver_version="1.2.3",
                error="wrong digests",
            ),
        ) as full_mock,
        patch("robo_rec.gpu.correctness_cache.default_cache_path", return_value=cache_path),
    ):
        report = probe_gpu_status()

    full_mock.assert_called_once()
    assert report.opencl_usable is False
    assert report.opencl_usability_cached is False
    assert report.gpu_present_but_unusable is True
    assert report.gpu_acceleration_available is False
    stored = cache.get_cached_verdict(_SIG, cache_path=cache_path)
    assert stored is not None and stored.usable is False


def test_report_cached_device_skips_full_probe(tmp_path):
    """The whole point of the cache: a second call for the same device/driver must not
    re-run the expensive correctness test."""
    cache_path = tmp_path / "gpu_config.json"
    cache.store_verdict(_SIG, usable=True, error=None, cache_path=cache_path)

    with (
        patch("robo_rec.gpu.report.probe_opencl", return_value=_opencl_available()),
        patch("robo_rec.gpu.report.probe_opencl_device_signature", return_value=_identity_ok()),
        patch("robo_rec.gpu.report.probe_opencl_correctness") as full_mock,
        patch("robo_rec.gpu.correctness_cache.default_cache_path", return_value=cache_path),
    ):
        report = probe_gpu_status()

    full_mock.assert_not_called()
    assert report.opencl_usable is True
    assert report.opencl_usability_cached is True
    assert report.gpu_acceleration_available is True
    assert report.gpu_present_but_unusable is False


def test_report_force_recheck_bypasses_cache_and_retests(tmp_path):
    cache_path = tmp_path / "gpu_config.json"
    cache.store_verdict(_SIG, usable=False, error="old failure", cache_path=cache_path)

    with (
        patch("robo_rec.gpu.report.probe_opencl", return_value=_opencl_available()),
        patch("robo_rec.gpu.report.probe_opencl_device_signature", return_value=_identity_ok()),
        patch(
            "robo_rec.gpu.report.probe_opencl_correctness",
            return_value=OpenClCorrectnessResult(
                usable=True,
                platform_name="Test Platform",
                device_name="Test Device",
                driver_version="1.2.3",
                error=None,
            ),
        ) as full_mock,
        patch("robo_rec.gpu.correctness_cache.default_cache_path", return_value=cache_path),
    ):
        report = probe_gpu_status(force_recheck=True)

    full_mock.assert_called_once()
    assert report.opencl_usable is True
    assert report.opencl_usability_cached is False
    stored = cache.get_cached_verdict(_SIG, cache_path=cache_path)
    assert stored is not None and stored.usable is True  # old "old failure" verdict replaced


def test_report_identity_failure_falls_back_to_uncached_full_probe():
    """If the identity probe can't even determine which device to key on (e.g. the
    subprocess itself failed), there's nothing to cache under — must still attempt the
    full probe rather than silently reporting unusable without trying."""
    with (
        patch("robo_rec.gpu.report.probe_opencl", return_value=_opencl_available()),
        patch(
            "robo_rec.gpu.report.probe_opencl_device_signature",
            return_value=_identity_missing(),
        ),
        patch(
            "robo_rec.gpu.report.probe_opencl_correctness",
            return_value=OpenClCorrectnessResult(
                usable=False,
                platform_name=None,
                device_name=None,
                driver_version=None,
                error="launch failed",
            ),
        ) as full_mock,
    ):
        report = probe_gpu_status()

    full_mock.assert_called_once()
    assert report.opencl_usable is False
    assert report.opencl_usability_cached is False
