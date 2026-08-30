print("Importing shutdown screen...")

from globals import DISPLAY
from ui.gui import CustomQWidget
from ui.waiting_spinner import QtWaitingSpinner

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout


class ShutdownScreen(CustomQWidget):
    """Terminal overlay shown while the app tears down; there is no hide/reset path back."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.spinner = QtWaitingSpinner()
        self.spinner.setParent(self)

        self.setMessage()
        self.__statusLabel.setAlignment(Qt.AlignCenter)
        self.__statusLabel.setStyleSheet("font-size: 30px; color: white;")

        rootLayout = QVBoxLayout()
        rootLayout.addStretch(1)
        rootLayout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        rootLayout.addWidget(self.__statusLabel, alignment=Qt.AlignCenter)
        rootLayout.addStretch(1)

        self.setFixedWidth(DISPLAY.WIDTH)
        self.setFixedHeight(DISPLAY.HEIGHT)
        self.setLayout(rootLayout)
        self.setStyleSheet("background-color: black;")
        self.hide()

    def start(self):
        self.spinner.start()

    def setMessage(self, msg=None):
        if msg is None:
            msg = "bro is shutting down..."
        self.__statusLabel.setText(msg)
