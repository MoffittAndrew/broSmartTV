print("Importing onscreen keyboard...")

from globals import DISPLAY
from ui.tools.button import Button
from ui.gui import CustomQWidget

from PyQt5.QtWidgets import QLabel, QGridLayout, QVBoxLayout


class OnScreenKeyboard(CustomQWidget):
    KEY_ROWS = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l", "@"],
        ["z", "x", "c", "v", "b", "n", "m", ".", "-", "_"],
    ]

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
        self.setStyleSheet("background-color: rgba(0, 0, 0, 242);")
        self.hide()

    def getPrimaryButton(self):
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

        controlsRowIndex = len(self.KEY_ROWS)
        self.__spaceButton = self._makeSpaceButton()
        self.__backspaceButton = self._makeActionButton("BKSP", self._backspace)
        self.__clearButton = self._makeActionButton("CLEAR", self._clear)
        self.__cancelButton = self._makeActionButton("CANCEL", self._cancel)
        self.__enterButton = self._makeActionButton("ENTER", self._submit)

        controlsRow = [
            self.__spaceButton,
            self.__backspaceButton,
            self.__clearButton,
            self.__cancelButton,
            self.__enterButton,
        ]

        self.__keyGrid.addWidget(self.__spaceButton, controlsRowIndex, 0, 1, 4)
        self.__keyGrid.addWidget(self.__backspaceButton, controlsRowIndex, 4, 1, 2)
        self.__keyGrid.addWidget(self.__clearButton, controlsRowIndex, 6, 1, 1)
        self.__keyGrid.addWidget(self.__cancelButton, controlsRowIndex, 7, 1, 1)
        self.__keyGrid.addWidget(self.__enterButton, controlsRowIndex, 8, 1, 2)

        for index in range(len(controlsRow) - 1):
            controlsRow[index].setNavRight(controlsRow[index + 1])
            controlsRow[index + 1].setNavLeft(controlsRow[index])

        bottomAlphaRow = self.__keyButtons[-1]
        bottomAnchors = [0, 4, 6, 7, 8]
        for index, controlButton in enumerate(controlsRow):
            upButton = bottomAlphaRow[bottomAnchors[index]]
            upButton.setNavDown(controlButton)
            controlButton.setNavUp(upButton)

        self.__primaryButton = self.__keyButtons[0][0]

    def _makeKeyButton(self, keyText, width=160):
        return Button(width=width, height=90, text=keyText, callback=self._addText, menuOptions=[], img=None, navUp=None, navRight=None, navDown=None, navLeft=None)

    def _makeSpaceButton(self):
        return Button(width=640, height=90, text="SPACE", callback=self._addText, menuOptions=[], img=None, navUp=None, navRight=None, navDown=None, navLeft=None)

    def _makeActionButton(self, text, callback):
        return Button(width=240, height=90, text=text, callback=callback, menuOptions=[], img=None, navUp=None, navRight=None, navDown=None, navLeft=None)

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
        self.__promptLabel.setText(str(prompt))
        self.__statusLabel.setText("")
        self._renderText()
        self.__isVisibleOverlay = True
        self.show()
        self.raise_()

    def closeOverlay(self):
        self.__isVisibleOverlay = False
        self.hide()

