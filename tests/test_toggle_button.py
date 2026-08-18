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


def test_toggle_button_reads_owner_state_after_click_callback():
    state = {"enabled": False}

    def fetch_value():
        return state["enabled"]

    async def toggle_owner_value():
        state["enabled"] = not state["enabled"]

    button = ToggleButton(
        fetchValueCallback=fetch_value,
        trueText="ON",
        falseText="OFF",
        clickCallback=toggle_owner_value,
    )

    assert button.getValue() is False
    assert button.getText() == "OFF"

    asyncio.run(button.click())

    assert state["enabled"] is True
    assert button.getValue() is True
    assert button.getText() == "ON"