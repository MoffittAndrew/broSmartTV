from globals import DISPLAY

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QSize

APP = QApplication([])

MAIN_WINDOW = QMainWindow()
MAIN_WINDOW.setWindowTitle("bro is literally a smart tv")
MAIN_WINDOW.setFixedSize(QSize(DISPLAY.WIDTH, DISPLAY.HEIGHT))