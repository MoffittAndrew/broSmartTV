# Set up the main window where the GUI magic happens

print("Importing GUI tools...")

from globals import DISPLAY, INPUT, GUI

from PyQt5 import sip
from PyQt5.QtWidgets import QWidget, QLabel, QStackedLayout
from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QKeyEvent, QImage, QPixmap

import asyncio
import inspect


class CustomQLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)

    def getAbsolutePos(self):
        window = self.window()
        if window is not None and isinstance(window, QWidget):
            return self.mapTo(window, QPoint(0, 0))
        return self.pos()


class CustomQWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)

    def getAbsolutePos(self):
        window = self.window()
        if window is not None and isinstance(window, QWidget):
            return self.mapTo(window, QPoint(0, 0))
        return self.pos()


class ScreenCastView(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: black;")
        self.setScaledContents(False)
        self.hide()

    def setFrame(self, frame):
        if frame is None:
            return

        height, width = frame.shape[:2]
        target_size = self.size()
        if frame.ndim == 3:
            rgb = frame if frame.flags.c_contiguous else frame.copy()
            image = QImage(
                sip.voidptr(rgb.ctypes.data),
                width,
                height,
                width * 3,
                QImage.Format_RGB888,
            )
        else:
            grayscale = frame if frame.flags.c_contiguous else frame.copy()
            image = QImage(
                sip.voidptr(grayscale.ctypes.data),
                width,
                height,
                width,
                QImage.Format_Grayscale8,
            )

        self._pixmap = QPixmap.fromImage(image)
        if not target_size.isEmpty() and self._pixmap.size() != target_size:
            self.setPixmap(self._pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.FastTransformation))
        else:
            self.setPixmap(self._pixmap)
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap is not None and not self._pixmap.isNull():
            self.setPixmap(self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.FastTransformation))


class CustomQWindow(QWidget):
    def __init__(self, keyboard=None, inputInterface=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setContentsMargins(0, 0, 0, 0)
        self.__layout = QStackedLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setStackingMode(QStackedLayout.StackAll)
        self.setKeyboard(keyboard)
        self.setInputInterface(inputInterface)
        self.__screenCastWidget = None
        self.__screenCastPreviousWidget = None
        from ui.tools.onscreen_keyboard import OnScreenKeyboard
        self.__onScreenKeyboard = OnScreenKeyboard(parent=self)
        self.__textInputPreviousSelection = None
        self.__textInputOnCancel = None
        self.addWidget(self.__onScreenKeyboard)
        self.__onScreenKeyboard.hide()

    def getKeyboard(self):
        return self.__keyboard

    def getDefaultTab(self):
        return self.__defaultTab

    def getTab(self):
        return self.__tab

    def getInputInterface(self):
        return self.__inputInterface

    def getOnScreenKeyboard(self):
        return self.__onScreenKeyboard

    def getAbsolutePos(self):
        return QPoint(0, 0)

    def setKeyboard(self, keyboard):
        self.__keyboard = keyboard

    def setDefaultTab(self, tab):
        self.__defaultTab = tab

    def setTab(self, tab=None):
        self.hideTextInput(cancelled=True)

        if tab is None:
            tab = self.getDefaultTab()

        if tab == self.getDefaultTab():
            tab.setTab()

        if isinstance(tab, QWidget):
            self.__layout.setCurrentWidget(tab)
        else:
            self.__tab = tab
            self.__layout.setCurrentIndex(self.getTab())

        inputInterface = self.getInputInterface()
        if inputInterface is not None:
            inputInterface.setSelectedButton(self.__layout.currentWidget().getPrimaryButton())
            self.__layout.setCurrentWidget(inputInterface)

    def setInputInterface(self, inputInterface):
        self.__inputInterface = inputInterface
        if inputInterface is not None:
            self.addWidget(inputInterface)

    def addWidget(self, widget):
        widget.setParent(self)
        self.__layout.addWidget(widget)
        self.setLayout(self.__layout)

    def openTextInput(
        self,
        prompt="Enter text",
        initialText="",
        masked=False,
        maxLength=64,
        onSubmit=None,
        onCancel=None,
    ):
        inputInterface = self.getInputInterface()
        if inputInterface is None:
            return

        self.__textInputPreviousSelection = inputInterface.getSelectedButton()
        self.__textInputOnCancel = onCancel

        def submitBridge(text):
            self._completeTextInput(
                onSubmit=onSubmit,
                onCancel=onCancel,
                submittedText=text,
                cancelled=False,
            )

        def cancelBridge():
            self._completeTextInput(
                onSubmit=onSubmit,
                onCancel=onCancel,
                submittedText=None,
                cancelled=True,
            )

        self.getOnScreenKeyboard().openOverlay(
            prompt=prompt,
            initialText=initialText,
            masked=masked,
            maxLength=maxLength,
            onSubmit=submitBridge,
            onCancel=cancelBridge,
        )
        keyboardPrimaryButton = self.getOnScreenKeyboard().getPrimaryButton()
        if keyboardPrimaryButton is not None:
            inputInterface.setSelectedButton(keyboardPrimaryButton)

    def hideTextInput(self, cancelled=False):
        if not self.getOnScreenKeyboard().isOverlayVisible():
            return

        self.getOnScreenKeyboard().closeOverlay()

        inputInterface = self.getInputInterface()
        if inputInterface is not None:
            restoreButton = self.__textInputPreviousSelection
            if restoreButton is not None:
                inputInterface.setSelectedButton(restoreButton)

        if cancelled and self.__textInputOnCancel is not None:
            result = self.__textInputOnCancel()
            if inspect.isawaitable(result):
                asyncio.ensure_future(result)

        self.__textInputOnCancel = None

    def _completeTextInput(self, onSubmit, onCancel, submittedText=None, cancelled=False):
        inputInterface = self.getInputInterface()
        self.hideTextInput(cancelled=False)

        if inputInterface is not None:
            restoreButton = self.__textInputPreviousSelection
            if restoreButton is None:
                currentWidget = self.__layout.currentWidget()
                if currentWidget is not None and hasattr(currentWidget, "getPrimaryButton"):
                    restoreButton = currentWidget.getPrimaryButton()
            if restoreButton is not None:
                inputInterface.setSelectedButton(restoreButton)

        callback = onCancel if cancelled else onSubmit
        if callback is not None:
            result = callback() if cancelled else callback(submittedText)
            if inspect.isawaitable(result):
                asyncio.ensure_future(result)

        self.__textInputOnCancel = None

    def setScreenCastWidget(self, widget):
        self.__screenCastWidget = widget
        if widget is not None:
            self.addWidget(widget)
            widget.hide()

    def showScreenCast(self):
        if self.__screenCastWidget is None:
            return

        if self.__screenCastPreviousWidget is None:
            self.__screenCastPreviousWidget = self.__layout.currentWidget()

        self.__screenCastWidget.setGeometry(0, 0, self.width(), self.height())
        self.__screenCastWidget.show()
        self.__screenCastWidget.raise_()
        self.__layout.setCurrentWidget(self.__screenCastWidget)

    def hideScreenCast(self):
        if self.__screenCastWidget is not None:
            self.__screenCastWidget.hide()

        if self.__screenCastPreviousWidget is not None:
            self.__layout.setCurrentWidget(self.__screenCastPreviousWidget)
            self.__screenCastPreviousWidget = None

    def keyPressEvent(self, event, *args, **kwargs):
        if self.getKeyboard() is not None:
            if isinstance(event, QKeyEvent):
                key = event.key()
                self.getKeyboard().receive(key)
        else:
            return super().keyPressEvent(event, *args, **kwargs)

    def keyReleaseEvent(self, event, *args, **kwargs):
        if self.getKeyboard() is not None:
            if isinstance(event, QKeyEvent):
                key = event.key()
                self.getKeyboard().receive(key, INPUT.RELEASED_PREFIX)
        else:
            return super().keyReleaseEvent(event, *args, **kwargs)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.__screenCastWidget is not None:
            self.__screenCastWidget.setGeometry(0, 0, self.width(), self.height())
        if self.__onScreenKeyboard is not None:
            self.__onScreenKeyboard.setGeometry(0, 0, self.width(), self.height())

    def show(self):
        super().show()
        self.setTab()


MAIN_WINDOW = CustomQWindow()
MAIN_WINDOW.setWindowTitle(DISPLAY.WINDOW_TITLE)
MAIN_WINDOW.setFixedSize(QSize(DISPLAY.WIDTH, DISPLAY.HEIGHT))

MAIN_WINDOW.setAutoFillBackground(True)
palette = MAIN_WINDOW.palette()
palette.setColor(MAIN_WINDOW.backgroundRole(), GUI.BG_COLOR)
MAIN_WINDOW.setPalette(palette)