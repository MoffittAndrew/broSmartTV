print("Importing reconnect screen...")

from globals import DISPLAY, GUI
from ui.gui import CustomQWidget
from ui.waiting_spinner import QtWaitingSpinner

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout


class ReconnectScreen(CustomQWidget):
    """Opaque terminal overlay shown while screen casting reconnects automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.spinner = QtWaitingSpinner()
        self.spinner.setParent(self)

        self.__statusLabel = QLabel()
        self.setMessage()
        self.__statusLabel.setAlignment(Qt.AlignCenter)
        self.__statusLabel.setStyleSheet("font-size: 30px; color: white;")

        rootLayout = QVBoxLayout()
        rootLayout.addStretch(1)
        rootLayout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        rootLayout.addSpacing(GUI.SPACING.WIDE * 3)
        rootLayout.addWidget(self.__statusLabel, alignment=Qt.AlignCenter)
        rootLayout.addStretch(1)

        self.setFixedWidth(DISPLAY.WIDTH)
        self.setFixedHeight(DISPLAY.HEIGHT)
        self.setLayout(rootLayout)
        # StackAll leaves other widgets visible, so this screen must paint an opaque background.
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)
        self.hide()

    def start(self):
        self.spinner.start()

    def stop(self):
        self.spinner.stop()

    def setMessage(self, msg=None):
        if msg is None:
            msg = "bro is reconnecting..."
        self.__statusLabel.setText(msg)
