print("Importing GUI tools...")

from globals import DISPLAY, INPUT

from PyQt5.QtWidgets import QWidget, QStackedLayout
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QKeyEvent

class CustomQWindow(QWidget):
    def __init__(this, keyboard = None, inputInterface = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.__layout = QStackedLayout()
        this.__layout.setContentsMargins(0, 0, 0, 0)
        this.__layout.setStackingMode(QStackedLayout.StackAll)
        this.setKeyboard(keyboard)
        this.setInputInterface(inputInterface)
        
    def getKeyboard(this):
        return this.__keyboard

    def getTab(this):
        return this.__tab
    
    def getInputInterface(this):
        return this.__inputInterface
        
    def setKeyboard(this, keyboard):
        this.__keyboard = keyboard
        
    def setTab(this, tab):
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

MAIN_WINDOW = CustomQWindow()
MAIN_WINDOW.setWindowTitle("bro is literally a smart tv")
MAIN_WINDOW.setFixedSize(QSize(DISPLAY.WIDTH, DISPLAY.HEIGHT))

MAIN_WINDOW.setAutoFillBackground(True)
p = MAIN_WINDOW.palette()
p.setColor(MAIN_WINDOW.backgroundRole(), Qt.black)
MAIN_WINDOW.setPalette(p)