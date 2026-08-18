from robo_rec.recovery.tokenlist import build_tokenlist_file
from robo_rec.util.paths import btcrecover_root


def test_tokenlist_matches_vendored_fixture_syntax():
    """Cross-check our generated syntax against btcrecover's own test fixture, which uses
    the identical ^N^word positional-anchor format (see
    vendor/btcrecover/btcrecover/test/test-listfiles/SeedTokenListTest.txt)."""
    fixture = (
        btcrecover_root() / "btcrecover" / "test" / "test-listfiles" / "SeedTokenListTest.txt"
    )
    fixture_lines = fixture.read_text().splitlines()
    anchored = [line for line in fixture_lines if line.startswith("^")]
    assert anchored[0] == "^1^ocean"
    assert anchored[-1] == "^9^spring"

    known = [None] * 12
    known[0] = "ocean"
    known[8] = "spring"
    path = build_tokenlist_file(known_words=known, scrambled_words=["convince", "attitude"])
    try:
        lines = path.read_text().splitlines()
        assert "^1^ocean" in lines
        assert "^9^spring" in lines
        assert "convince" in lines
        assert "attitude" in lines
    finally:
        path.unlink()


def test_tokenlist_unanchored_lines_have_no_caret():
    known = [None] * 12
    known[0] = "rotate"
    path = build_tokenlist_file(known_words=known, scrambled_words=["dream", "drip"])
    try:
        lines = path.read_text().splitlines()
        assert "dream" in lines
        assert "drip" in lines
        assert not any(line.startswith("^") and "dream" in line for line in lines)
    finally:
        path.unlink()
