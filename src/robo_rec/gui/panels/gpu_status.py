"""GPU Status panel — wired to robo_rec.gpu via GpuProbeWorker (PRD 4.5).

Shows NVIDIA driver/CUDA toolkit presence, OpenCL device availability, and PyCUDA
importability, with a JSON export so the client can send diagnostics back to the developer
(the developer's own hardware has no discrete GPU, so real-world validation depends on this
export — PRD 4.5/6.3).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from robo_rec.gpu.report import GpuStatusReport, export_json
from robo_rec.gui.gpu_worker import GpuProbeWorker
from robo_rec.gui.icons import load_pixmap
from robo_rec.gui.panels.base_panel import BasePanel
from robo_rec.gui.theme import ACCENT, TEXT_SECONDARY


class GpuStatusPanel(BasePanel):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "GPU Status",
            "Robo-Rec detects NVIDIA GPU acceleration automatically — this view shows "
            "what it found, and lets you export a diagnostics report.",
            parent,
        )

        self._worker: GpuProbeWorker | None = None
        self._latest_report: GpuStatusReport | None = None
        self._on_report_ready = None  # optional callback set by MainWindow

        summary_row = QHBoxLayout()
        summary_row.setSpacing(10)
        self._summary_icon = QLabel()
        summary_row.addWidget(self._summary_icon)
        self._summary_label = QLabel("Checking for a GPU…")
        self._summary_label.setObjectName("DashboardTitle")
        summary_row.addWidget(self._summary_label)
        summary_row.addStretch(1)
        self.root_layout.addLayout(summary_row)

        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)
        self._nvidia_label = QLabel()
        self._nvidia_label.setWordWrap(True)
        details_layout.addWidget(self._nvidia_label)
        self._opencl_label = QLabel()
        self._opencl_label.setWordWrap(True)
        details_layout.addWidget(self._opencl_label)
        self._pycuda_label = QLabel()
        self._pycuda_label.setWordWrap(True)
        details_layout.addWidget(self._pycuda_label)
        self.root_layout.addWidget(details_group)

        self._errors_label = QLabel()
        self._errors_label.setObjectName("InfoNotice")
        self._errors_label.setWordWrap(True)
        self._errors_label.hide()
        self.root_layout.addWidget(self._errors_label)

        buttons_row = QHBoxLayout()
        self._refresh_button = QPushButton("Re-check GPU")
        self._refresh_button.clicked.connect(self._start_probe)
        buttons_row.addWidget(self._refresh_button)

        self._export_button = QPushButton("Export Diagnostics (JSON)")
        self._export_button.setObjectName("PrimaryButton")
        self._export_button.clicked.connect(self._on_export_clicked)
        self._export_button.setEnabled(False)
        buttons_row.addWidget(self._export_button)
        buttons_row.addStretch(1)
        self.root_layout.addLayout(buttons_row)

        self.root_layout.addStretch(1)

        self._start_probe()

    def _start_probe(self) -> None:
        self._refresh_button.setEnabled(False)
        self._summary_label.setText("Checking for a GPU…")
        self._summary_icon.setPixmap(load_pixmap("loader-circle", TEXT_SECONDARY, 20))
        self._worker = GpuProbeWorker()
        self._worker.finished.connect(self._on_report_finished)
        self._worker.start()

    def shutdown(self) -> None:
        """Called from MainWindow.closeEvent: wait for any in-flight probe so its
        background QThread doesn't get destroyed while still running. GPU probes have no
        cancel() (they're not long-running searches) — just join whatever's in flight."""
        if self._worker is not None:
            self._worker.wait_and_cleanup()
            self._worker = None

    def _on_report_finished(self, report: GpuStatusReport) -> None:
        self._latest_report = report
        self._refresh_button.setEnabled(True)
        self._export_button.setEnabled(True)
        if self._worker is not None:
            self._worker.wait_and_cleanup()
            self._worker = None

        if report.gpu_acceleration_available:
            self._summary_icon.setPixmap(load_pixmap("cpu", ACCENT, 20))
            self._summary_label.setText("GPU acceleration available")
        else:
            self._summary_icon.setPixmap(load_pixmap("cpu", TEXT_SECONDARY, 20))
            self._summary_label.setText("No GPU acceleration — running on CPU")

        if report.nvidia_gpu_name:
            self._nvidia_label.setText(
                f"NVIDIA: {report.nvidia_gpu_name}  ·  driver {report.nvidia_driver_version}"
                + (f"  ·  CUDA {report.cuda_toolkit_version}" if report.cuda_toolkit_version else "")
            )
        else:
            self._nvidia_label.setText("NVIDIA: no driver detected")

        if report.opencl_devices:
            device_names = ", ".join(d.name for d in report.opencl_devices)
            self._opencl_label.setText(f"OpenCL devices: {device_names}")
        else:
            self._opencl_label.setText("OpenCL: no devices available")

        self._pycuda_label.setText(
            "PyCUDA: importable" if report.pycuda_importable else "PyCUDA: not available"
        )

        if report.probe_errors:
            self._errors_label.setText(
                "Diagnostics:\n" + "\n".join(f"• {err}" for err in report.probe_errors)
            )
            self._errors_label.show()
        else:
            self._errors_label.hide()

        if self._on_report_ready is not None:
            self._on_report_ready(report.gpu_acceleration_available)

    def set_report_callback(self, callback) -> None:
        """Optional hook so MainWindow can update its top-bar GPU badge from real data."""
        self._on_report_ready = callback

    def _on_export_clicked(self) -> None:
        if self._latest_report is None:
            return
        default_name = "robo-rec-gpu-diagnostics.json"
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export GPU Diagnostics", default_name, "JSON files (*.json)"
        )
        if not path_str:
            return
        try:
            export_json(self._latest_report, Path(path_str))
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        QMessageBox.information(self, "Exported", f"Diagnostics saved to:\n{path_str}")
