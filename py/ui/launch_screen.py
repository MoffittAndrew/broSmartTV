from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget

from ui.waiting_spinner import QtWaitingSpinner
from ui.update_log_display import UpdateLogDisplay
from app_logging import LogRecord, get_logger


class LaunchScreen(QWidget):
    """Simple launch screen container with spinner and rolling update log."""

    log_record_received = pyqtSignal(object)

    def __init__(self, display, log_font_size=30, log_max_lines=15, margin=40, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Launching...")
        self.setFixedSize(QSize(display.WIDTH, display.HEIGHT))
        self.setContentsMargins(0, 0, 0, 0)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)

        self.spinner = QtWaitingSpinner()
        self.spinner.setParent(self)
        self.spinner.start()

        self.log_display = UpdateLogDisplay(max_lines=log_max_lines, parent=self)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(log_font_size)
        self.log_display.setFont(font)

        label_height = min(220, max(120, display.HEIGHT // 3))
        self.log_display.setGeometry(
            margin,
            display.HEIGHT - label_height - margin,
            display.WIDTH - (2 * margin),
            label_height,
        )
        self.log_display.setText("Waiting for update output...")

        self.log_record_received.connect(self._append_log_record)
        self._logger = get_logger()
        self._unsubscribe = self._logger.subscribe(
            self._receive_log_record,
            categories=("startup", "update"),
        )
        for record in self._logger.history(categories=("startup", "update")):
            self._append_log_record(record)

    def _receive_log_record(self, record: LogRecord):
        """Forward background-thread events to a slot owned by the Qt thread."""
        self.log_record_received.emit(record)

    def _append_log_record(self, record: LogRecord):
        self.log_display.append_line(self._logger.format(record))

    def append_log_line(self, line):
        """Keep the old API for callers outside the logger migration."""
        self.log_display.append_line(line)

    def stop(self):
        self.spinner.stop()

    def closeEvent(self, event):
        self._unsubscribe()
        super().closeEvent(event)
