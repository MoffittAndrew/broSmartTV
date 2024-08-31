print("Importing GUI tools...")

from globals import DISPLAY, INPUT

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QKeyEvent

class CustomQMainWindow(QMainWindow):
    def __init__(this, keyboard = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.setKeyboard(keyboard)
        
    def getKeyboard(this):
        return this.__keyboard
        
    def setKeyboard(this, keyboard):
        this.__keyboard = keyboard
    
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

MAIN_WINDOW = CustomQMainWindow()
MAIN_WINDOW.setWindowTitle("bro is literally a smart tv")
MAIN_WINDOW.setFixedSize(QSize(DISPLAY.WIDTH, DISPLAY.HEIGHT))