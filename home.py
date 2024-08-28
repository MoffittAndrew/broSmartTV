from PyQt5 import QtWidgets
from navbar import navBar

class HomeScreen(QtWidgets.QtWidget):
    def __init__(this, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        
        layout.addWidget(navBar)
        
        this.setLayout(layout)