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
        # A plain stylesheet background doesn't reliably paint on this custom-widget base, which
        # let the home screen show through underneath; autoFillBackground+palette (like
        # LaunchScreen/MAIN_WINDOW) guarantees an opaque background instead.
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)
        self.hide()

    def setVerse(self, verse):
        self.__verseLabel.setText(f"\u201c{verse.text}\u201d")
        self.__referenceLabel.setText(verse.reference)
        # Re-rolled on every show so repeated launches don't always land on the same button text.
        self.__okButton.setText(random.choice(BIBLE_VERSE.OK_BUTTON_NAMES))
        # setText() only flags the button dirty; it must be redrawn explicitly to actually repaint.
        self.__okButton.draw()
        self.__okButton.update()

    def showVerse(self, verse):
        """Set the verse and make this screen visible - MAIN_WINDOW's stacked layout runs in
        StackAll mode, so widgets must be shown/hidden explicitly (see web_interface.py's
        openURL()/closeAndReturnHome() for the same pattern) rather than relying on tab switches."""
        self.setVerse(verse)
        self.show()

    def getPrimaryButton(self):
        return self.__okButton

    async def _onOk(self):
        self.hide()
        MAIN_WINDOW.setTab()


bibleVerseScreen = BibleVerseScreen()
