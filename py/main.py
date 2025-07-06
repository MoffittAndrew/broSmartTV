print("Starting...")

print("Starting imports...")
from gui import APP, MAIN_WINDOW
from input_interface import inputInterface
#from web_interface import webInterface
from home import homeScreen
from remote import remote
from keyboard import keyboard

import asyncio
import qtinter
print("Completed imports.")

def main():
    with qtinter.using_asyncio_from_qt():  # <-- enable asyncio in qt code
        asyncio.create_task(remote.init())
        print("Starting GUI...")
        MAIN_WINDOW.show()
        APP.exec_()
        print("App closed.")
        remote.setRunning(False)


MAIN_WINDOW.setInputInterface(inputInterface)
MAIN_WINDOW.addWidget(homeScreen)
#MAIN_WINDOW.addWidget(webInterface)

keyboard.setInputInterface(inputInterface)
remote.setInputInterface(inputInterface)
MAIN_WINDOW.setKeyboard(keyboard)

MAIN_WINDOW.setTab(homeScreen)

print("Running main event loop...")
main()
print("Exiting...")