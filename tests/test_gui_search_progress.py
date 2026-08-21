"""SearchProgressWidget replaced each recovery panel's bespoke loading view: a clean
cycling-dots title animation (no rotating/flickering icon) plus a read-only summary of the
submitted seed phrase and target wallet/address.
"""

from __future__ import annotations

from robo_rec.gui.widgets.search_progress import SearchProgressWidget

WORDS = ["rotate", "dream", "drip", "opinion", "key", "dove", "region", "mind", "visit", "diesel", "negative", "speed"]


def test_start_populates_summary(qtbot):
    widget = SearchProgressWidget("Searching")
    qtbot.addWidget(widget)

    widget.start(
        subtitle="Estimated time: under a minute.",
        summary_words=WORDS,
        target_summary="Bitcoin (BTC)  ·  1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6",
    )

    assert widget._summary_seed_row.words() == WORDS
    assert "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6" in widget._summary_target_label.text()
    assert widget._subtitle_label.text() == "Estimated time: under a minute."


def test_start_shows_blank_tiles_for_missing_words(qtbot):
    widget = SearchProgressWidget("Searching")
    qtbot.addWidget(widget)

    words_with_blank = WORDS.copy()
    words_with_blank[4] = ""
    widget.start(subtitle="", summary_words=words_with_blank, target_summary="")

    assert widget._summary_seed_row.words()[4] == ""


def test_title_cycles_through_dot_frames_and_wraps():
    widget = SearchProgressWidget("Searching")
    widget.start(subtitle="", summary_words=WORDS, target_summary="")
    base = widget._title_label.text()
    assert base == "Searching"

    widget._advance_dots()
    assert widget._title_label.text() == "Searching."
    widget._advance_dots()
    assert widget._title_label.text() == "Searching.."
    widget._advance_dots()
    assert widget._title_label.text() == "Searching..."
    widget._advance_dots()
    assert widget._title_label.text() == "Searching"  # wraps back to no dots


def test_stop_halts_the_dot_timer():
    widget = SearchProgressWidget("Searching")
    widget.start(subtitle="", summary_words=WORDS, target_summary="")
    assert widget._dot_timer.isActive()
    widget.stop()
    assert not widget._dot_timer.isActive()


def test_set_phase_and_subtitle_update_labels():
    widget = SearchProgressWidget("Searching")
    widget.start(subtitle="initial", summary_words=WORDS, target_summary="")
    widget.set_subtitle("updated subtitle")
    widget.set_phase("Phase 2/4: ...")
    assert widget._subtitle_label.text() == "updated subtitle"
    assert widget._phase_label.text() == "Phase 2/4: ..."
