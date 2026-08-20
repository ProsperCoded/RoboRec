"""End-to-end GUI integration tests: real form input -> real BtcrecoverRunner subprocess ->
real result displayed in the panel. Uses the same disposable known-good mnemonic/address
pair verified throughout this project's terminal testing (robo-rec-implementation.md).
"""

from __future__ import annotations

from robo_rec.gui.main_window import MainWindow

MNEMONIC = "rotate dream drip opinion key dove region mind visit diesel negative speed"
WORDS = MNEMONIC.split()
BTC_ADDRESS = "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6"


def test_missing_words_panel_recovers_real_blank_via_ui(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    panel = window._missing_words_panel

    panel._seed_row.set_words([w if i != 4 else "" for i, w in enumerate(WORDS)])
    panel._address_field.setText(BTC_ADDRESS)
    panel._known_radio.setChecked(True)
    panel._refresh_missing_count()
    assert panel._start_button.isEnabled()

    panel._on_proceed_clicked()
    qtbot.waitUntil(lambda: panel._view_stack.currentIndex() == 2, timeout=15000)

    assert panel._result_row.words() == WORDS
    window.close()


def test_derive_wallet_panel_derives_real_address_via_ui(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    panel = window._derive_wallet_panel

    panel._seed_row.set_words(WORDS)
    panel._token_combo.setCurrentText("Bitcoin (BTC)")
    panel._on_derive_clicked()

    # Note: isVisible() reflects the whole ancestor chain, which is never actually shown
    # in this headless test (the window is only constructed, never .show()'d) — checking
    # the derived address content itself is a more direct, environment-independent signal
    # that _on_derive_clicked() genuinely called into robo_rec.derivation.
    displayed_text = panel._result_group.findChildren(type(panel._address_field))
    addresses = [w.text() for w in displayed_text if w.text()]
    assert BTC_ADDRESS in addresses
    window.close()


def test_derive_wallet_panel_verifies_target_address_via_ui(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    panel = window._derive_wallet_panel

    panel._seed_row.set_words(WORDS)
    panel._token_combo.setCurrentText("Bitcoin (BTC)")
    panel._address_field.setText(BTC_ADDRESS)
    panel._on_derive_clicked()

    displayed_text = panel._result_group.findChildren(type(panel._address_field))
    addresses = [w.text() for w in displayed_text if w.text()]
    assert BTC_ADDRESS in addresses
    window.close()


def test_gpu_status_panel_shows_real_probe_result(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    panel = window._gpu_status_panel

    qtbot.waitUntil(lambda: panel._latest_report is not None, timeout=15000)
    # This dev machine has no discrete GPU (robo-rec-implementation.md) — confirms the
    # panel is reading the real probe_gpu_status() result, not a mock.
    assert panel._latest_report.opencl_available is False
    assert panel._export_button.isEnabled()
    window.close()


def test_gpu_status_panel_shows_real_cpu_details_when_no_gpu(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    panel = window._gpu_status_panel

    qtbot.waitUntil(lambda: panel._latest_report is not None, timeout=15000)
    # No discrete GPU on this dev machine, so the CPU details section should be shown
    # and populated with real platform data (robo-rec-implementation.md).
    assert panel._latest_report.gpu_acceleration_available is False
    assert panel._cpu_group.isVisibleTo(panel)
    assert panel._cpu_cores_label.text()
    assert panel._cpu_os_label.text()
    window.close()


def test_typo_correction_panel_recovers_real_typo_via_ui(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    panel = window._typo_correction_panel

    # "negative" -> a spelling-neighbor typo, matches the approach validated in
    # robo-rec-implementation.md Section 4.1.
    from robo_rec.util.mnemonic import close_words

    typo_index, substitute = None, None
    for i, word in enumerate(WORDS):
        neighbors = [w for w in close_words(word, cutoff=0.5, limit=5) if w != word]
        if neighbors:
            typo_index, substitute = i, neighbors[0]
            break
    assert typo_index is not None, "expected at least one spelling-neighbor in this phrase"

    typed = WORDS.copy()
    typed[typo_index] = substitute
    panel._seed_row.set_words(typed)
    panel._address_field.setText(BTC_ADDRESS)

    panel._on_proceed_clicked()
    qtbot.waitUntil(lambda: panel._view_stack.currentIndex() == 2, timeout=15000)

    assert panel._result_row.words() == WORDS
    window.close()


def test_rearrange_panel_recovers_real_scramble_via_ui(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    panel = window._rearrange_panel

    # Lock the first 8 words in their correct positions; leave the last 4 scrambled
    # (4! = 24 permutations — fast, matches the pattern already validated in
    # tests/test_recovery_runner.py::test_rearrangement_end_to_end).
    panel._seed_row.set_words(WORDS)
    for tile in panel._seed_row.tiles()[:8]:
        tile.set_locked(True)
    panel._seed_row.locks_changed.emit()
    panel._address_field.setText(BTC_ADDRESS)

    panel._on_proceed_clicked()
    qtbot.waitUntil(lambda: panel._view_stack.currentIndex() == 2, timeout=15000)

    assert panel._result_row.words() == WORDS
    window.close()


def test_unsupported_coin_shows_warning_instead_of_crashing(qtbot, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    window = MainWindow()
    qtbot.addWidget(window)
    panel = window._derive_wallet_panel

    shown = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: shown.append(a)))

    panel._seed_row.set_words(WORDS)
    panel._token_combo.setCurrentText("Other BIP39-compatible")
    panel._on_derive_clicked()

    assert shown, "expected a warning dialog for the unsupported coin option"
    window.close()


def test_gpu_badge_click_navigates_to_gpu_status_panel(qtbot):
    from PySide6.QtCore import Qt

    window = MainWindow()
    qtbot.addWidget(window)
    assert window._stack.currentWidget() is window._dashboard

    qtbot.mouseClick(window._gpu_badge, Qt.MouseButton.LeftButton)

    assert window._stack.currentWidget() is window._gpu_status_panel
    window.close()
