from navbar import navBar
from tilegrid import tileGrid

from PyQt5.QtWidgets import QWidget, QVBoxLayout

class HomeScreen(QWidget):
    def __init__(this, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout()
        
        layout.addWidget(navBar)
        layout.addWidget(tileGrid)
        
        this.setLayout(layout)