from html import escape
import re

from PyQt5.QtWidgets import QLabel


class UpdateLogDisplay(QLabel):
    """A rolling on-screen log display with simple per-line color coding."""

    def __init__(self, max_lines=15, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_lines = max_lines
        self._lines = []

        self.setWordWrap(True)
        self.setStyleSheet("color: white;")

    def clear_lines(self):
        self._lines = []
        self.setText("")

    def append_line(self, line):
        line = str(line).strip()
        if not line:
            return

        self._lines.append(line)
        self._lines = self._lines[-self._max_lines:]
        self.setText(self._build_rich_text(self._lines))

    def _get_line_color(self, line):
        lower_line = line.lower()

        exit_match = re.search(r"exited with code\s+(-?\d+)", lower_line)
        if exit_match is not None:
            return "#8BE28B" if int(exit_match.group(1)) == 0 else "#FF7A7A"

        if any(token in lower_line for token in ["error", "failed", "fatal", "exception", "traceback"]):
            return "#FF7A7A"

        if any(token in lower_line for token in ["warn", "warning", "skip", "retry"]):
            return "#FFD166"

        if any(token in lower_line for token in ["done", "finished", "reloaded", "connected", "updated"]):
            return "#8BE28B"

        return "#FFFFFF"

    def _build_rich_text(self, lines):
        rendered_lines = []
        for line in lines:
            color = self._get_line_color(line)
            rendered_lines.append(f'<span style="color: {color};">{escape(line)}</span>')
        return "<br>".join(rendered_lines)
