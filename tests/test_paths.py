from unittest.mock import patch

from robo_rec.util import paths


def test_is_compiled_detects_nuitka_module_marker():
    with patch.dict(paths.__dict__, {"__compiled__": object()}):
        assert paths.is_compiled() is True
