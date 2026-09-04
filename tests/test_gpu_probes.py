import subprocess
from unittest.mock import patch

from robo_rec.gpu.cpu_probe import probe_cpu
from robo_rec.gpu.nvidia_probe import NvidiaProbeResult, probe_nvidia
from robo_rec.gpu.opencl_probe import OpenClProbeResult, probe_opencl
from robo_rec.gpu.pycuda_probe import probe_pycuda_importable
from robo_rec.gpu.report import probe_gpu_status


def test_probe_gpu_status_degrades_gracefully_with_no_gpu():
    """The no-GPU behavior must not depend on the machine running the tests."""
    with (
        patch(
            "robo_rec.gpu.report.probe_opencl",
            return_value=OpenClProbeResult(available=False, devices=[], error=None),
        ),
        patch(
            "robo_rec.gpu.report.probe_nvidia",
            return_value=NvidiaProbeResult(None, None, None, "nvidia-smi not found"),
        ),
        patch("robo_rec.gpu.report.probe_pycuda_importable", return_value=False),
    ):
        report = probe_gpu_status()
    assert report.opencl_available is False
    assert report.nvidia_driver_version is None
    assert report.pycuda_importable is False
    assert report.probe_errors == ["NVIDIA: nvidia-smi not found"]
    assert report.gpu_acceleration_available is False


def test_probe_gpu_status_always_includes_cpu_info():
    report = probe_gpu_status()
    assert report.cpu_info.architecture
    assert report.cpu_info.os_name
    assert report.cpu_info.logical_cores is not None and report.cpu_info.logical_cores > 0


def test_probe_cpu_returns_real_values():
    info = probe_cpu()
    assert info.architecture
    assert info.os_name
    assert info.logical_cores is not None and info.logical_cores > 0


def test_probe_nvidia_reports_missing_binary_cleanly():
    with patch("robo_rec.gpu.nvidia_probe.shutil.which", return_value=None):
        result = probe_nvidia()
    assert result.driver_version is None
    assert result.error is not None
    assert "nvidia-smi" in result.error


def test_probe_nvidia_parses_mocked_query_output():
    fake_query = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="NVIDIA GeForce RTX 3080, 535.104.05\n", stderr=""
    )
    fake_header = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="CUDA Version: 12.2 \n", stderr=""
    )
    with (
        patch("robo_rec.gpu.nvidia_probe.shutil.which", return_value="/usr/bin/nvidia-smi"),
        patch("robo_rec.gpu.nvidia_probe.subprocess.run", side_effect=[fake_query, fake_header]),
    ):
        result = probe_nvidia()
    assert result.gpu_name == "NVIDIA GeForce RTX 3080"
    assert result.driver_version == "535.104.05"
    assert result.cuda_toolkit_version == "12.2"


def test_probe_opencl_returns_unavailable_on_nonzero_exit():
    fake = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="Traceback...\n")
    with patch("robo_rec.gpu.opencl_probe.subprocess.run", return_value=fake):
        result = probe_opencl()
    assert result.available is False
    assert result.error is not None


def test_probe_opencl_returns_unavailable_when_pyopencl_missing():
    """Mirrors btcrpass.get_opencl_devices()'s own caught ImportError path — the
    detection script reports this as a clean {"ok": False, "error": ...} JSON payload,
    not a crash, matching how get_opencl_devices() itself degrades."""
    fake = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"ok": false, "error": "ImportError: No module named \'pyopencl\'"}\n',
        stderr="",
    )
    with patch("robo_rec.gpu.opencl_probe.subprocess.run", return_value=fake):
        result = probe_opencl()
    assert result.available is False
    assert result.devices == []
    assert "pyopencl" in result.error


def test_probe_opencl_parses_real_devices_from_json():
    fake = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            '{"ok": true, "devices": ['
            '{"platform": "NVIDIA CUDA", "index": 0, "name": "GeForce RTX 3080"}, '
            '{"platform": "NVIDIA CUDA", "index": 1, "name": "GeForce RTX 3070"}'
            "]}\n"
        ),
        stderr="",
    )
    with patch("robo_rec.gpu.opencl_probe.subprocess.run", return_value=fake):
        result = probe_opencl()
    assert result.available is True
    assert len(result.devices) == 2
    assert result.devices[0].name == "GeForce RTX 3080"
    assert result.devices[0].platform_id == result.devices[1].platform_id  # same platform
    assert result.devices[1].device_id == 1


def test_probe_opencl_no_devices_found_is_unavailable_not_error():
    """get_opencl_devices() returns an empty list (no error) when pyopencl loaded fine
    but found no supported hardware (its own caught 'platform not found' LogicError
    case) — the probe must treat that as unavailable-but-clean, not as a failure."""
    fake = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='{"ok": true, "devices": []}\n', stderr=""
    )
    with patch("robo_rec.gpu.opencl_probe.subprocess.run", return_value=fake):
        result = probe_opencl()
    assert result.available is False
    assert result.devices == []
    assert result.error is None


def test_probe_pycuda_importable_false_when_absent():
    with patch("robo_rec.gpu.pycuda_probe.importlib.util.find_spec", return_value=None):
        assert probe_pycuda_importable() is False
