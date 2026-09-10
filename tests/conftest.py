"""Shared, autouse test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True, scope="session")
def _isolate_gpu_correctness_cache(tmp_path_factory):
    """Every test that (directly or via MainWindow's startup probe) calls
    probe_gpu_status() ends up writing a verdict through
    robo_rec.gpu.correctness_cache — without this, running the test suite from source
    would leave a real gpu_config.json in the repo root as a side effect.

    Session-scoped, not per-test: several test files (test_gui_navigation.py,
    test_gui_shutdown.py, test_smoke.py) each instantiate MainWindow, which fires a
    real OpenCL correctness probe (an actual subprocess that compiles and runs a GPU
    kernel) unless a verdict for this machine's device is already cached. Sharing one
    temp path across the whole session means that real, slow probe only ever runs
    once — every MainWindow() after the first one gets a cache hit, same as a real
    second app launch would.

    Tests in test_gpu_correctness.py that need to control caching precisely mostly
    pass their own cache_path explicitly (or patch this same function locally with
    their own tmp_path) and are unaffected by this broader default.
    """
    from robo_rec.gpu import correctness_cache

    path = tmp_path_factory.mktemp("gpu-correctness-cache") / "gpu_config.json"
    original = correctness_cache.default_cache_path
    correctness_cache.default_cache_path = lambda: path
    try:
        yield path
    finally:
        correctness_cache.default_cache_path = original
