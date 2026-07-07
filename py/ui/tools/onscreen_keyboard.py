print("Importing onscreen keyboard...")

from globals import DISPLAY
from ui.tools.button import Button
from ui.gui import CustomQWidget

from PyQt5.QtWidgets import QLabel, QGridLayout, QVBoxLayout


class OnScreenKeyboard(CustomQWidget):
    KEY_ROWS = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "@"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l", ".", ","],
        ["z", "x", "c", "v", "b", "n", "m", "<", ">", "/", "?"],
    ]

    CAPS_SYMBOL_NUMBER_ROW = ["!", '"', "£", "$", "%", "^", "&", "*", "(", ")", "#"]
    EXTRA_SYMBOL_ROW = ["_", "-", ".", ",", "@", "~", "\\", "/", "?", ":", ";"]

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
        self.__maxLength = 64
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

        self.__keyGrid = QGridLayout()
        self.__keyGrid.setHorizontalSpacing(10)
        self.__keyGrid.setVerticalSpacing(10)

        self._buildKeyGrid()

        rootLayout = QVBoxLayout()
        rootLayout.setContentsMargins(80, 40, 80, 40)
        rootLayout.setSpacing(24)
        rootLayout.addWidget(self.__promptLabel)
        rootLayout.addWidget(self.__textLabel)
        rootLayout.addWidget(self.__statusLabel)
        rootLayout.addLayout(self.__keyGrid)
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
        previousRow = None

        for rowIndex, row in enumerate(self.KEY_ROWS):
            buttonRow = []
            for columnIndex, keyText in enumerate(row):
                button = self._makeKeyButton(keyText, width=160)
                self.__keyGrid.addWidget(button, rowIndex, columnIndex)
                buttonRow.append(button)

                if columnIndex > 0:
                    leftButton = buttonRow[columnIndex - 1]
                    leftButton.setNavRight(button)
                    button.setNavLeft(leftButton)

                if previousRow is not None and columnIndex < len(previousRow):
                    upButton = previousRow[columnIndex]
                    upButton.setNavDown(button)
                    button.setNavUp(upButton)

            self.__keyButtons.append(buttonRow)
            previousRow = buttonRow

        self.__symbolButtons = []
        symbolRowIndex = len(self.KEY_ROWS)
        for columnIndex, keyText in enumerate(self.EXTRA_SYMBOL_ROW):
            button = self._makeKeyButton(keyText, width=160)
            self.__keyGrid.addWidget(button, symbolRowIndex, columnIndex)
            self.__symbolButtons.append(button)

            if columnIndex > 0:
                leftButton = self.__symbolButtons[columnIndex - 1]
                leftButton.setNavRight(button)
                button.setNavLeft(leftButton)

            if previousRow is not None and columnIndex < len(previousRow):
                upButton = previousRow[columnIndex]
                upButton.setNavDown(button)
                button.setNavUp(upButton)

        previousRow = self.__symbolButtons

        controlsRowIndex = len(self.KEY_ROWS) + 1
        self.__capsButton = self._makeActionButton("CAPS OFF", self._toggleCaps, width=320)
        self.__spaceButton = self._makeSpaceButton()
        self.__backspaceButton = self._makeActionButton("BKSP", self._backspace, width=320)
        self.__clearButton = self._makeActionButton("CLEAR", self._clear, width=160)
        self.__cancelButton = self._makeActionButton("CANCEL", self._cancel, width=160)
        self.__enterButton = self._makeActionButton("ENTER", self._submit, width=160)

        controlsRow = [
            self.__capsButton,
            self.__spaceButton,
            self.__backspaceButton,
            self.__clearButton,
            self.__cancelButton,
            self.__enterButton,
        ]

        self.__keyGrid.addWidget(self.__capsButton, controlsRowIndex, 0, 1, 2)
        self.__keyGrid.addWidget(self.__spaceButton, controlsRowIndex, 2, 1, 4)
        self.__keyGrid.addWidget(self.__backspaceButton, controlsRowIndex, 6, 1, 2)
        self.__keyGrid.addWidget(self.__clearButton, controlsRowIndex, 8, 1, 1)
        self.__keyGrid.addWidget(self.__cancelButton, controlsRowIndex, 9, 1, 1)
        self.__keyGrid.addWidget(self.__enterButton, controlsRowIndex, 10, 1, 1)

        for index in range(len(controlsRow) - 1):
            controlsRow[index].setNavRight(controlsRow[index + 1])
            controlsRow[index + 1].setNavLeft(controlsRow[index])

        bottomAlphaRow = previousRow
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

    def _makeKeyButton(self, keyText, width=160):
        return Button(width=width, height=90, text=keyText, callback=self._addText, menuOptions=[], img=None, navUp=None, navRight=None, navDown=None, navLeft=None)

    def _makeSpaceButton(self):
        return Button(width=640, height=90, text="SPACE", callback=self._addText, menuOptions=[], img=None, navUp=None, navRight=None, navDown=None, navLeft=None)

    def _makeActionButton(self, text, callback, width=240):
        return Button(width=width, height=90, text=text, callback=callback, menuOptions=[], img=None, navUp=None, navRight=None, navDown=None, navLeft=None)

    def _applyCapsState(self):
        numberRow = self.CAPS_SYMBOL_NUMBER_ROW if self.__capsEnabled else self.KEY_ROWS[0]
        for columnIndex, button in enumerate(self.__keyButtons[0]):
            button.setText(numberRow[columnIndex])
            button.draw()

        for rowIndex in range(1, len(self.KEY_ROWS)):
            for columnIndex, button in enumerate(self.__keyButtons[rowIndex]):
                baseText = self.KEY_ROWS[rowIndex][columnIndex]
                if baseText.isalpha():
                    button.setText(baseText.upper() if self.__capsEnabled else baseText.lower())
                else:
                    button.setText(baseText)
                button.draw()

        self.__capsButton.setText("CAPS ON" if self.__capsEnabled else "CAPS OFF")
        self.__capsButton.draw()

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
        maxLength=64,
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

