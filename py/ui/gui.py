# Set up the main window where the GUI magic happens

print("Importing GUI tools...")

from globals import DISPLAY, INPUT, GUI

from PyQt5.QtWidgets import QWidget, QLabel, QStackedLayout
from PyQt5.QtCore import QSize, QPoint
from PyQt5.QtGui import QKeyEvent

class CustomQLabel(QLabel):
    def __init__(this, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.setContentsMargins(0, 0, 0, 0)
    
    def getAbsolutePos(this):
        if this.parent() is not None:
            return this.parent().getAbsolutePos() + this.pos()
        else:
            return this.pos()

class CustomQWidget(QWidget):
    def __init__(this, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.setContentsMargins(0, 0, 0, 0)
    
    def getAbsolutePos(this):
        if this.parent() is not None:
            return this.parent().getAbsolutePos() + this.pos()
        else:
            return this.pos()

class CustomQWindow(QWidget):
    def __init__(this, keyboard = None, inputInterface = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.setContentsMargins(0, 0, 0, 0)
        this.__layout = QStackedLayout()
        this.__layout.setContentsMargins(0, 0, 0, 0)
        this.__layout.setStackingMode(QStackedLayout.StackAll)
        this.setKeyboard(keyboard)
        this.setInputInterface(inputInterface)
    
    def getKeyboard(this):
        return this.__keyboard
    
    def getDefaultTab(this):
        return this.__defaultTab

    def getTab(this):
        return this.__tab
    
    def getInputInterface(this):
        return this.__inputInterface

    def getAbsolutePos(this):
        return QPoint(0, 0)
    
    def setKeyboard(this, keyboard):
        this.__keyboard = keyboard
    
    def setDefaultTab(this, tab):
        this.__defaultTab = tab
    
    def setTab(this, tab=None):
        if tab is None:
            tab = this.getDefaultTab()
        
        if tab == this.getDefaultTab():
            tab.setTab()
        
        if isinstance(tab, QWidget):
            this.__layout.setCurrentWidget(tab)
        else:
            this.__tab = tab
            this.__layout.setCurrentIndex(this.getTab())
        
        inputInterface = this.getInputInterface()
        if inputInterface is not None:
            inputInterface.setSelectedButton(this.__layout.currentWidget().getPrimaryButton())
            this.__layout.setCurrentWidget(inputInterface)
    
    def setInputInterface(this, inputInterface):
        this.__inputInterface = inputInterface
        if inputInterface is not None:
            this.addWidget(inputInterface)
    
    def addWidget(this, widget):
        widget.setParent(this)
        this.__layout.addWidget(widget)
        this.setLayout(this.__layout)

    def keyPressEvent(this, event, *args, **kwargs):
        if this.getKeyboard() is not None:
            if isinstance(event, QKeyEvent):
                key = event.key()
                this.getKeyboard().receive(key)
        else:
            return super().keyPressEvent(event, *args, **kwargs)
    
    def keyReleaseEvent(this, event, *args, **kwargs):
        if this.getKeyboard() is not None:
            if isinstance(event, QKeyEvent):
                key = event.key()
                this.getKeyboard().receive(key, INPUT.RELEASED_PREFIX)
        else:
            return super().keyReleaseEvent(event, *args, **kwargs)
    
    def show(this):
        super().show()
        this.setTab()

MAIN_WINDOW = CustomQWindow()
MAIN_WINDOW.setWindowTitle(DISPLAY.WINDOW_TITLE)
MAIN_WINDOW.setFixedSize(QSize(DISPLAY.WIDTH, DISPLAY.HEIGHT))

MAIN_WINDOW.setAutoFillBackground(True)
palette = MAIN_WINDOW.palette()
palette.setColor(MAIN_WINDOW.backgroundRole(), GUI.BG_COLOR)
MAIN_WINDOW.setPalette(palette)