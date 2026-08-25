from PySide6.QtGui import QIcon

from robo_rec.main import APP_ICON, APP_USER_MODEL_ID


def test_application_icon_is_bundled_and_loadable():
    assert APP_ICON.is_file()
    assert not QIcon(str(APP_ICON)).isNull()


def test_windows_app_id_is_stable():
    assert APP_USER_MODEL_ID == "RoboRec.Desktop"
