import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from robo_rec.gui.main_window import MainWindow

APP_USER_MODEL_ID = "RoboRec.Desktop"
APP_ICON = Path(__file__).parent / "gui" / "assets" / "app-icon.svg"


def _set_windows_app_id() -> None:
    """Give Windows a stable identity for taskbar grouping and icon selection."""
    if sys.platform != "win32":
        return

    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)


def main() -> int:
    # Nuitka one-file builds re-enter this executable to isolate OpenCL driver
    # enumeration from the GUI process.  Handle that mode before creating Qt.
    from robo_rec.gpu.opencl_probe import OPENCL_PROBE_HELPER_ARG, run_opencl_probe_helper

    if OPENCL_PROBE_HELPER_ARG in sys.argv[1:]:
        return run_opencl_probe_helper()

    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("RoboRec")
    app.setApplicationDisplayName("RoboRec")
    app.setOrganizationName("RoboRec")
    app.setWindowIcon(QIcon(str(APP_ICON)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
