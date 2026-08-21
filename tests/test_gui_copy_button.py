"""CopyButton copies its configured text to the clipboard on click, and shows a brief
checkmark confirmation before reverting to the copy icon."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from robo_rec.gui.widgets.copy_button import CopyButton


def test_click_copies_text_to_clipboard(qtbot):
    button = CopyButton("hello world")
    qtbot.addWidget(button)

    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

    assert QApplication.clipboard().text() == "hello world"


def test_set_text_to_copy_updates_target(qtbot):
    button = CopyButton("initial")
    qtbot.addWidget(button)
    button.set_text_to_copy("updated")
    button.click()
    assert QApplication.clipboard().text() == "updated"


def test_empty_text_does_not_touch_clipboard(qtbot):
    QApplication.clipboard().setText("untouched")
    button = CopyButton("")
    qtbot.addWidget(button)
    button.click()
    assert QApplication.clipboard().text() == "untouched"


def test_click_shows_confirmation_then_reverts(qtbot):
    button = CopyButton("copy me")
    qtbot.addWidget(button)
    button.click()
    assert button.toolTip() == "Copied!"
    assert button._revert_timer.isActive()

    button._revert_icon()
    assert button.toolTip() == "Copy to clipboard"
