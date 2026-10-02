import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

from PyQt5.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

from ui.gui import ScreenCastView


def test_reset_stops_queued_render_callback_from_rescheduling(monkeypatch):
    view = ScreenCastView()
    scheduled_delays = []
    monkeypatch.setattr(view, "_scheduleRender", lambda: scheduled_delays.append(True))

    view.setFrame(object(), arrival_time=0)
    assert view._render_loop_active is True

    view.resetSyncHoldback()
    view._renderPendingFrame()

    assert view._render_loop_active is False
    assert scheduled_delays == [True]
