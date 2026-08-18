import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import launch_signals


def test_consume_skip_standby_is_true_once_then_false(tmp_path):
    flag_path = str(tmp_path / "skip-standby.flag")

    assert launch_signals.consume_skip_standby(flag_path) is False

    launch_signals.request_skip_standby(flag_path)
    assert launch_signals.consume_skip_standby(flag_path) is True
    assert launch_signals.consume_skip_standby(flag_path) is False


def test_consume_exit_code_resets_to_default_after_consume():
    launch_signals.request_exit_code(201)

    assert launch_signals.consume_exit_code() == 201
    assert launch_signals.consume_exit_code(default=0) == 0
