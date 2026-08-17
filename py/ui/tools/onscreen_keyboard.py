print("Importing onscreen keyboard...")

from globals import DISPLAY, GUI
from ui.tools.button import Button
from ui.gui import CustomQWidget
from ui.tools.section import HSection, GridSection

from PyQt5.QtWidgets import QLabel, QVBoxLayout


class OnScreenKeyboard(CustomQWidget):

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.__keyButtons = []
        self.__primaryButton = None
        self.__text = ""
        self.__masked = False
        self.__maxLength = GUI.KEYBOARD.MAX_LENGTH
        self.__isVisibleOverlay = False
        self.__capsEnabled = False

        self.__submitCallback = None
        self.__cancelCallback = None

        self.__promptLabel = QLabel("Enter text")
        self.__promptLabel.setStyleSheet("font-size: 36px; font-weight: bold; color: white;")

        self.__textLabel = QLabel("")
        self.__textLabel.setStyleSheet(
            "font-size: 34px; color: white; border: 2px solid white; padding: 18px; background: rgba(15, 15, 15, 220);"
        )
        self.__textLabel.setWordWrap(True)
        self.__textLabel.setMinimumHeight(120)

        self.__statusLabel = QLabel("")
        self.__statusLabel.setStyleSheet("font-size: 24px; color: #f5d56d;")

        self.__keyGridSection = GridSection(columns=len(GUI.KEYBOARD.KEY_ROWS[0]), spacing=GUI.SPACING.TIGHT)

        self._buildKeyGrid()

        rootLayout = QVBoxLayout()
        rootLayout.setContentsMargins(*GUI.MARGINS.OVERLAY)
        rootLayout.setSpacing(GUI.SPACING.NORMAL)
        rootLayout.addWidget(self.__promptLabel)
        rootLayout.addWidget(self.__textLabel)
        rootLayout.addWidget(self.__statusLabel)
        rootLayout.addWidget(self.__keyGridSection)
        rootLayout.addWidget(self.__controlsSection)
        rootLayout.addStretch(1)

        self.setFixedWidth(DISPLAY.WIDTH)
        self.setFixedHeight(DISPLAY.HEIGHT)
        self.setLayout(rootLayout)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 190);")
        self.hide()

    def getPrimaryButton(self):
        if self.__primaryButton is None and len(self.__keyButtons) > 0 and len(self.__keyButtons[0]) > 0:
            self.__primaryButton = self.__keyButtons[0][0]
        return self.__primaryButton

    def isOverlayVisible(self):
        return self.__isVisibleOverlay

    def getText(self):
        return self.__text

    def _buildKeyGrid(self):
        self.__keyButtons = []

        for row in GUI.KEYBOARD.KEY_ROWS:
            buttonRow = []
            for keyText in row:
                button = self._makeKeyButton(keyText)
                buttonRow.append(button)

            self.__keyButtons.append(buttonRow)

        self.__symbolButtons = []
        for keyText in GUI.KEYBOARD.EXTRA_SYMBOL_ROW:
            button = self._makeKeyButton(keyText)
            self.__symbolButtons.append(button)

        self.__capsButton = self._makeActionButton("CAPS OFF", self._toggleCaps, width=GUI.KEYBOARD.BUTTON_WIDTH * 2)
        self.__spaceButton = self._makeSpaceButton()
        self.__backspaceButton = self._makeActionButton("DELETE", self._backspace, width=GUI.KEYBOARD.BUTTON_WIDTH * 2)
        self.__clearButton = self._makeActionButton("CLEAR", self._clear, width=GUI.KEYBOARD.BUTTON_WIDTH)
        self.__cancelButton = self._makeActionButton("CANCEL", self._cancel, width=GUI.KEYBOARD.BUTTON_WIDTH)
        self.__enterButton = self._makeActionButton("ENTER", self._submit, width=GUI.KEYBOARD.BUTTON_WIDTH)

        controlsRow = [
            self.__capsButton,
            self.__spaceButton,
            self.__backspaceButton,
            self.__clearButton,
            self.__cancelButton,
            self.__enterButton,
        ]

        self.__controlsSection = HSection(widgets=controlsRow, spacing=GUI.SPACING.TIGHT)

        allRows = []
        allRows.extend(self.__keyButtons)
        allRows.append(self.__symbolButtons)

        gridWidgets = []
        for row in allRows:
            gridWidgets.extend(row)
        self.__keyGridSection.setWidgets(gridWidgets)

        bottomAlphaRow = self.__symbolButtons
        controlByColumn = [
            self.__capsButton,
            self.__capsButton,
            self.__spaceButton,
            self.__spaceButton,
            self.__spaceButton,
            self.__spaceButton,
            self.__backspaceButton,
            self.__backspaceButton,
            self.__clearButton,
            self.__cancelButton,
            self.__enterButton,
        ]

        for columnIndex, upButton in enumerate(bottomAlphaRow):
            controlButton = controlByColumn[columnIndex]
            upButton.setNavDown(controlButton)

        controlUpMap = {
            self.__capsButton: bottomAlphaRow[0],
            self.__spaceButton: bottomAlphaRow[2],
            self.__backspaceButton: bottomAlphaRow[6],
            self.__clearButton: bottomAlphaRow[8],
            self.__cancelButton: bottomAlphaRow[9],
            self.__enterButton: bottomAlphaRow[10],
        }
        for controlButton, upButton in controlUpMap.items():
            controlButton.setNavUp(upButton)

        self.__primaryButton = self.__keyButtons[0][0]
        self._applyCapsState()

    def _makeKeyButton(self, keyText):
        return Button(width=GUI.KEYBOARD.BUTTON_WIDTH, height=GUI.KEYBOARD.BUTTON_HEIGHT, text=keyText, clickCallback=self._addText, menuCallback=self._toggleCaps)

    def _makeSpaceButton(self):
        return Button(width=GUI.KEYBOARD.SPACEBAR_WIDTH, height=GUI.KEYBOARD.BUTTON_HEIGHT, text="SPACE", clickCallback=self._addText, menuCallback=self._toggleCaps)

    def _makeActionButton(self, text, clickCallback, width=GUI.KEYBOARD.BUTTON_WIDTH):
        return Button(width=width, height=GUI.KEYBOARD.BUTTON_HEIGHT, text=text, clickCallback=clickCallback, menuCallback=self._toggleCaps)

    def _applyCapsState(self):
        numberRow = GUI.KEYBOARD.CAPS_SYMBOL_NUMBER_ROW if self.__capsEnabled else GUI.KEYBOARD.KEY_ROWS[0]
        for columnIndex, button in enumerate(self.__keyButtons[0]):
            button.setText(numberRow[columnIndex])
            button.draw()

        for rowIndex in range(1, len(GUI.KEYBOARD.KEY_ROWS)):
            for columnIndex, button in enumerate(self.__keyButtons[rowIndex]):
                baseText = GUI.KEYBOARD.KEY_ROWS[rowIndex][columnIndex]
                if baseText.isalpha():
                    button.setText(baseText.upper() if self.__capsEnabled else baseText.lower())
                else:
                    button.setText(baseText)
                button.draw()

        self.__capsButton.setText("CAPS ON" if self.__capsEnabled else "CAPS OFF")
        self.__capsButton.draw()
        self._redrawAllButtons()

    def _redrawAllButtons(self):
        for row in self.__keyButtons:
            for button in row:
                button.draw()
                button.update()

        for button in self.__symbolButtons:
            button.draw()
            button.update()

        controls = [
            self.__capsButton,
            self.__spaceButton,
            self.__backspaceButton,
            self.__clearButton,
            self.__cancelButton,
            self.__enterButton,
        ]
        for button in controls:
            button.draw()
            button.update()

    async def _toggleCaps(self):
        self.__capsEnabled = not self.__capsEnabled
        self._applyCapsState()

    def _renderText(self):
        visibleText = self.__text
        if self.__masked:
            visibleText = "*" * len(self.__text)

        if visibleText == "":
            visibleText = " "
        self.__textLabel.setText(visibleText)

    async def _addText(self):
        selectedButton = None
        window = self.window()
        if window is not None and hasattr(window, "getInputInterface"):
            inputInterface = window.getInputInterface()
            if inputInterface is not None:
                selectedButton = inputInterface.getSelectedButton()

        if selectedButton is None:
            return

        keyText = selectedButton.getText()
        if keyText == "SPACE":
            keyText = " "

        if len(self.__text) >= self.__maxLength:
            self.__statusLabel.setText(f"Maximum {self.__maxLength} characters")
            return

        self.__statusLabel.setText("")
        self.__text += keyText
        self._renderText()

    async def _backspace(self):
        self.__statusLabel.setText("")
        if len(self.__text) > 0:
            self.__text = self.__text[:-1]
            self._renderText()

    async def _clear(self):
        self.__statusLabel.setText("")
        self.__text = ""
        self._renderText()

    async def _cancel(self):
        self.closeOverlay()
        if self.__cancelCallback is not None:
            self.__cancelCallback()

    async def _submit(self):
        submittedText = self.__text
        self.closeOverlay()
        if self.__submitCallback is not None:
            self.__submitCallback(submittedText)

    def openOverlay(
        self,
        prompt="Enter text",
        initialText="",
        masked=False,
        onSubmit=None,
        onCancel=None,
        maxLength=GUI.KEYBOARD.MAX_LENGTH,
    ):
        self.__submitCallback = onSubmit
        self.__cancelCallback = onCancel
        self.__masked = bool(masked)
        self.__maxLength = max(1, int(maxLength))
        self.__text = str(initialText)
        self.__capsEnabled = False
        self.__promptLabel.setText(str(prompt))
        self.__statusLabel.setText("")
        self._applyCapsState()
        self._renderText()
        self.getPrimaryButton()
        self.__isVisibleOverlay = True
        self.show()
        self.raise_()

    def closeOverlay(self):
        self.__isVisibleOverlay = False
        self.hide()

