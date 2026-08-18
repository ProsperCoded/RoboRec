from robo_rec.recovery.parser import parse_line

# Lines below are verbatim captures from real seedrecover.py runs (see robo-rec-implementation.md
# and this session's terminal verification), not invented fixtures.


def test_phase_line():
    event = parse_line(
        "2026-08-19 00:03:24 : Phase 2/4: 1 mistake which can be an entirely different seed word."
    )
    assert event.kind == "phase"
    assert event.phase_current == 2
    assert event.phase_total == 4


def test_eta_line_seconds():
    event = parse_line("Will try 2,048 passwords, ETA 1 seconds ...")
    assert event.kind == "eta"
    assert event.eta_seconds == 1


def test_eta_line_hours_minutes():
    event = parse_line("Will try 4,194,304 passwords, ETA 2 hours 5 minutes 1 seconds ...")
    assert event.kind == "eta"
    assert event.eta_seconds == 2 * 3600 + 5 * 60 + 1


def test_matching_seed_found_line():
    event = parse_line(
        "2026-08-19 00:03:24 : ***MATCHING SEED FOUND***, "
        "Matched on Address at derivation path: m/44'/0'/0'/0/0"
    )
    assert event.kind == "found"
    assert event.result is not None
    assert event.result.matched_path == "m/44'/0'/0'/0/0"


def test_seed_found_line_captures_mnemonic():
    event = parse_line(
        "Seed found: rotate dream drip opinion key dove region mind visit diesel negative speed"
    )
    assert event.kind == "found"
    assert event.result is not None
    assert event.result.mnemonic == (
        "rotate dream drip opinion key dove region mind visit diesel negative speed"
    )
    assert event.result.succeeded is True


def test_not_found_line_mid_phase():
    event = parse_line(" Seed not found")
    assert event.kind == "not_found"


def test_not_found_line_final():
    event = parse_line(" Seed not found, sorry...")
    assert event.kind == "not_found"


def test_unrecognized_line_becomes_log_event():
    event = parse_line("Using the 'en' wordlist.")
    assert event.kind == "log"
    assert event.message == "Using the 'en' wordlist."
