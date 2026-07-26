from robo_rec.main import MainWindow


def test_main_window_creates(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "Robo-Rec"
