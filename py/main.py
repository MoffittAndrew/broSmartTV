print("Starting...")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    APP = QApplication([])

print("Starting imports...")
from gui import MAIN_WINDOW
from interface.input_interface import inputInterface
#from interface.web_interface import webInterface
from interface.remote_interface import remoteInterface
from interface.keyboard_interface import keyboardInterface
from interface.projector_interface import projectorInterface
from home import homeScreen

import asyncio
import qtinter
print("Completed imports.")

def main():
    with qtinter.using_asyncio_from_qt():  # <-- enable asyncio in qt code
        asyncio.create_task(remoteInterface.connect())
        print("Starting GUI...")
        MAIN_WINDOW.show()
        APP.exec_()
        print("App closed.")

MAIN_WINDOW.setInputInterface(inputInterface)
MAIN_WINDOW.addWidget(homeScreen)
homeScreen.setPos((500, 500))
#MAIN_WINDOW.addWidget(webInterface)

inputInterface.setProjectorInterface(projectorInterface)
keyboardInterface.setInputInterface(inputInterface)
remoteInterface.setInputInterface(inputInterface)
MAIN_WINDOW.setKeyboard(keyboardInterface)

MAIN_WINDOW.setTab(homeScreen)

if __name__ == "__main__":
    print("Running main event loop...")
    main()
    print("Exiting...")