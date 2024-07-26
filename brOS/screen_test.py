from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

# Only needed for access to command line arguments
import sys

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

screen = app.primaryScreen()
rect = screen.availableGeometry()

# Create a Qt widget, which will be our window.
window = QMainWindow()
window.setFixedSize(QSize(rect.width(), rect.height()))
button = QPushButton("Press Me!")
window.setCentralWidget(button)
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()