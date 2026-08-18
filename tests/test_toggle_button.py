import asyncio
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

from PyQt5.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

import ui.gui
from ui.tools.button import ToggleButton


def test_toggle_button_reads_and_updates_owner_state():
    state = {"enabled": False}
    requested_values = []

    def fetch_value():
        return state["enabled"]

    def set_value(value):
        requested_values.append(value)
        state["enabled"] = value

    button = ToggleButton(
        fetchValueCallback=fetch_value,
        toggleCallback=set_value,
        trueText="ON",
        falseText="OFF",
    )

    assert button.getValue() is False
    assert button.getText() == "OFF"

    asyncio.run(button.click())

    assert requested_values == [True]
    assert state["enabled"] is True
    assert button.getValue() is True
    assert button.getText() == "ON"