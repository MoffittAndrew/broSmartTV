from navbar import navBar
from tilegrid import tileGrid

from PyQt5 import QtWidgets

class HomeScreen(QtWidgets.QWidget):
    def __init__(this, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        
        layout.addWidget(navBar)
        layout.addWidget(tileGrid)
        
        this.setLayout(layout)