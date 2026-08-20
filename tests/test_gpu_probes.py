import subprocess
from unittest.mock import patch

from robo_rec.gpu.cpu_probe import probe_cpu
from robo_rec.gpu.nvidia_probe import probe_nvidia
from robo_rec.gpu.opencl_probe import _parse_devices, probe_opencl
from robo_rec.gpu.pycuda_probe import probe_pycuda_importable
from robo_rec.gpu.report import probe_gpu_status


def test_probe_gpu_status_degrades_gracefully_with_no_gpu():
    """This is this dev machine's actual live state (no discrete GPU) — see
    robo-rec-implementation.md and PRD Section 6.1. Every probe must fail without raising."""
    report = probe_gpu_status()
    assert report.opencl_available is False
    assert report.nvidia_driver_version is None
    assert report.pycuda_importable is False
    assert len(report.probe_errors) == 3  # CPU probe has no failure mode, adds none
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
    fake = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="NameError: name 'opencl_information' is not defined\n"
    )
    with patch("robo_rec.gpu.opencl_probe.subprocess.run", return_value=fake):
        result = probe_opencl()
    assert result.available is False
    assert result.error is not None


def test_parse_devices_from_sample_output():
    sample = "Platform 0: NVIDIA CUDA\nDevice 0: GeForce RTX 3080\nDevice 1: GeForce RTX 3070\n"
    devices = _parse_devices(sample)
    assert len(devices) == 2
    assert devices[0].name == "GeForce RTX 3080"
    assert devices[1].device_id == 1


def test_probe_pycuda_importable_false_when_absent():
    # pycuda isn't a project dependency and isn't installed in this environment.
    assert probe_pycuda_importable() is False
