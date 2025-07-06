import sys
from PyQt5.QtWidgets import *

if __name__ == "__main__":
    app = QApplication([])

    w = QWidget()

    grid = QGridLayout(w)
    grid.addWidget(QPushButton("Button one"),0,0)
    grid.addWidget(QPushButton("Button two"),0,1)
    grid.addWidget(QPushButton("Button three"),1,0)
    grid.addWidget(QPushButton("Button four"),1,1)


    w.show()
    sys.exit(app.exec_())