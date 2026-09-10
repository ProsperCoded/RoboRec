from pathlib import Path
from unittest.mock import patch

from robo_rec.gui.recovery_worker import RecoveryWorker
from robo_rec.recovery.models import MissingWordKnownPositionSpec

REPO = Path(__file__).resolve().parents[1]
MNEMONIC = "rotate dream drip opinion key dove region mind visit diesel negative speed"
WORDS = MNEMONIC.split()
ADDRESS = "1FMHvVtJkJFnSxaN9KUn5q3KtqNwej1sZ6"


def test_unexpected_error_emits_failed_instead_of_hanging(qtbot):
    words = list(WORDS)
    words[4] = None
    spec = MissingWordKnownPositionSpec(words=words, wallet_type="bip39", addrs=[ADDRESS])
    with patch(
        "robo_rec.recovery.runner.build_missing_word_known_position_args",
        side_effect=FileNotFoundError("english.txt"),
    ):
        worker = RecoveryWorker(spec)
        with qtbot.waitSignal(worker.failed, timeout=5000) as blocker:
            worker.start()
        worker.wait_and_cleanup()
    assert "english.txt" in blocker.args[0]


def test_both_build_stages_bundle_bip_utils_wordlists():
    for name in ("compile.ps1", "compile.sh", "compile.bat", "build.py"):
        text = (REPO / name).read_text(encoding="utf-8")
        roborec_stage, engine_stage = text.split("--output-filename=Roborec", 1)
        assert "--include-package-data=bip_utils" in roborec_stage, name
        assert "--include-package-data=bip_utils" in engine_stage, name
