print("Importing bible verse screen...")

import random

from globals import DISPLAY, BIBLE_VERSE
from ui.gui import CustomQWidget, MAIN_WINDOW
from ui.tools.button import Button

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QLabel, QVBoxLayout


class BibleVerseScreen(CustomQWidget):
    """Shown once at startup with a random verse; OK button hands off to the home screen."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__verseLabel = QLabel()
        self.__verseLabel.setAlignment(Qt.AlignCenter)
        self.__verseLabel.setWordWrap(True)
        # Verse text comes straight from the Bible API; QLabel's default AutoText format will
        # sniff stray "<"/"&" in some translations' text as HTML and silently mangle/truncate
        # the render (including our appended closing quote), so force plain text.
        self.__verseLabel.setTextFormat(Qt.PlainText)
        self.__verseLabel.setStyleSheet("font-size: 44px; font-style: italic; color: white;")
        self.__verseLabel.setFixedWidth(DISPLAY.WIDTH - 240)

        self.__referenceLabel = QLabel()
        self.__referenceLabel.setAlignment(Qt.AlignCenter)
        self.__referenceLabel.setTextFormat(Qt.PlainText)
        self.__referenceLabel.setStyleSheet("font-size: 28px; color: white;")

        self.__okButton = Button(clickCallback=self._onOk, width=int(DISPLAY.WIDTH/2))

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
        text = f"\u201c{verse.text}\u201d"
        self.__verseLabel.setText(text)
        # QVBoxLayout doesn't reliably recompute a word-wrapped QLabel's height after a later
        # setText() call, which was silently clipping the last line (see LOGGING.md-adjacent
        # bug report: verses cut off mid-sentence with no closing quote). Measuring and setting
        # the height explicitly from font metrics avoids depending on that layout timing.
        boundingRect = QFontMetrics(self.__verseLabel.font()).boundingRect(
            0, 0, self.__verseLabel.width(), 0,
            Qt.TextWordWrap | Qt.AlignCenter,
            text,
        )
        self.__verseLabel.setFixedHeight(boundingRect.height() + 20)
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
