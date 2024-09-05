print("Importing GUI tools...")

from globals import DISPLAY, INPUT

from PyQt5.QtWidgets import QApplication, QWidget, QStackedLayout
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QKeyEvent

class CustomQWindow(QWidget):
    def __init__(this, keyboard = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.__layout = QStackedLayout()
        this.__layout.setContentsMargins(0, 0, 0, 0)
        this.setTab(0)
        this.setKeyboard(keyboard)
        
    def getKeyboard(this):
        return this.__keyboard

    def getTab(this):
        return this.__tab
        
    def setKeyboard(this, keyboard):
        this.__keyboard = keyboard
        
    def setTab(this, index):
        this.__tab = index
        this.__layout.setCurrentIndex(this.getTab())
        
    def addWidget(this, widget):
        this.__layout.addWidget(widget)
        this.setLayout(this.__layout)
    
    def keyPressEvent(this, event, *args, **kwargs):
        if this.getKeyboard() != None:
            if isinstance(event, QKeyEvent):
                key = event.key()
                this.getKeyboard().receive(key)
        else:
            return super().keyPressEvent(event, *args, **kwargs)
    
    def keyReleaseEvent(this, event, *args, **kwargs):
        if this.getKeyboard() != None:
            if isinstance(event, QKeyEvent):
                key = event.key()
                this.getKeyboard().receive(key, INPUT.RELEASED_PREFIX)
        else:
            return super().keyReleaseEvent(event, *args, **kwargs)
        
    

APP = QApplication([])

MAIN_WINDOW = CustomQWindow()
MAIN_WINDOW.setWindowTitle("bro is literally a smart tv")
MAIN_WINDOW.setFixedSize(QSize(DISPLAY.WIDTH, DISPLAY.HEIGHT))

