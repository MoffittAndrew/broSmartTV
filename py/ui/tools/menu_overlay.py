print("Importing menu overlay...")

from globals import DISPLAY, GUI
from ui.gui import CustomQWidget
from ui.tools.button import Button
from ui.tools.section import VSection

from PyQt5.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout


class MenuOverlay(CustomQWidget):
    """Generic dimmed-backdrop popup listing selectable options; reusable beyond branch switching."""

    def __init__(self, onClose=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__onClose = onClose
        self.__optionButtons = []
        self.__primaryButton = None

        self.__titleLabel = QLabel("")
        self.__titleLabel.setStyleSheet("font-size: 40px; font-weight: bold; color: white;")

        self.__messageLabel = QLabel("")
        self.__messageLabel.setWordWrap(True)
        self.__messageLabel.setStyleSheet("font-size: 24px; color: white;")
        self.__messageLabel.hide()

        self.__optionsSection = VSection(spacing=GUI.SPACING.NORMAL)

        self.__menuBox = CustomQWidget()
        self.__menuBox.setStyleSheet(
            f"background-color: rgb(20, 20, 20); border-radius: {GUI.BUTTON.ROUNDNESS}px;"
        )
        menuBoxLayout = QVBoxLayout()
        menuBoxLayout.setContentsMargins(*GUI.MARGINS.OVERLAY)
        menuBoxLayout.setSpacing(GUI.SPACING.WIDE)
        menuBoxLayout.addWidget(self.__titleLabel)
        menuBoxLayout.addWidget(self.__messageLabel)
        menuBoxLayout.addWidget(self.__optionsSection)
        self.__menuBox.setLayout(menuBoxLayout)

        # Standard Qt nested-stretch trick to center a fixed-size widget in a full-size overlay.
        centerRow = QHBoxLayout()
        centerRow.addStretch(1)
        centerRow.addWidget(self.__menuBox)
        centerRow.addStretch(1)

        outerLayout = QVBoxLayout()
        outerLayout.setContentsMargins(0, 0, 0, 0)
        outerLayout.addStretch(1)
        outerLayout.addLayout(centerRow)
        outerLayout.addStretch(1)

        self.setFixedWidth(DISPLAY.WIDTH)
        self.setFixedHeight(DISPLAY.HEIGHT)
        self.setLayout(outerLayout)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.hide()

    def getPrimaryButton(self):
        return self.__primaryButton

    def isOverlayVisible(self):
        return self.isVisible()

    def setOptions(self, options):
        buttons = []
        for option in options:
            button = Button(text=option["text"], width=GUI.MENU.BUTTON_WIDTH, height=GUI.MENU.BUTTON_HEIGHT)
            button.setClickCallback(option["clickCallback"])
            # Every option can back out of the menu without triggering its clickCallback.
            button.setReturnCallback(self.hideOverlay)
            buttons.append(button)

        self.__optionsSection.setWidgets(buttons)
        self.__optionButtons = buttons
        self.__primaryButton = buttons[0] if buttons else None

    async def showOverlay(self, title="", message="", options=None):
        self.__titleLabel.setText(title)
        self.__messageLabel.setText(message)
        self.__messageLabel.setVisible(bool(message))

        self.setOptions(options or [])

        self.show()
        self.raise_()

    async def hideOverlay(self):
        self.hide()
        if self.__onClose is not None:
            self.__onClose()
