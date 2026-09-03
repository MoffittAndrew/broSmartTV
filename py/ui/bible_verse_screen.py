print("Importing bible verse screen...")

import random

from globals import DISPLAY, BIBLE_VERSE
from ui.gui import CustomQWidget, MAIN_WINDOW
from ui.tools.button import Button

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout


class BibleVerseScreen(CustomQWidget):
    """Shown once at startup with a random verse; OK button hands off to the home screen."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__verseLabel = QLabel()
        self.__verseLabel.setAlignment(Qt.AlignCenter)
        self.__verseLabel.setWordWrap(True)
        self.__verseLabel.setStyleSheet("font-size: 44px; font-style: italic; color: white;")
        self.__verseLabel.setFixedWidth(DISPLAY.WIDTH - 240)

        self.__referenceLabel = QLabel()
        self.__referenceLabel.setAlignment(Qt.AlignCenter)
        self.__referenceLabel.setStyleSheet("font-size: 28px; color: white;")

        self.__okButton = Button(clickCallback=self._onOk)

        rootLayout = QVBoxLayout()
        rootLayout.addStretch(1)
        rootLayout.addWidget(self.__verseLabel, alignment=Qt.AlignCenter)
        rootLayout.addWidget(self.__referenceLabel, alignment=Qt.AlignCenter)
        rootLayout.addStretch(1)
        rootLayout.addWidget(self.__okButton, alignment=Qt.AlignCenter)
        rootLayout.addSpacing(60)

        self.setFixedWidth(DISPLAY.WIDTH)
        self.setFixedHeight(DISPLAY.HEIGHT)
        self.setLayout(rootLayout)
        self.setStyleSheet("background-color: black;")
        self.hide()

    def setVerse(self, verse):
        self.__verseLabel.setText(f"\u201c{verse.text}\u201d")
        self.__referenceLabel.setText(verse.reference)
        # Re-rolled on every show so repeated launches don't always land on the same button text.
        self.__okButton.setText(random.choice(BIBLE_VERSE.OK_BUTTON_NAMES))

    def getPrimaryButton(self):
        return self.__okButton

    async def _onOk(self):
        MAIN_WINDOW.setTab()


bibleVerseScreen = BibleVerseScreen()
