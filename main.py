print("Starting...")

print("Starting imports...")
from gui import APP, MAIN_WINDOW
from input_interface import inputInterface
from web_interface import webInterface
from home import homeScreen
from remote import remote
from keyboard import keyboard

import asyncio
print("Completed imports.")

async def main():
    await remote.init()
    print("Starting GUI...")
    APP.exec_()
    print("App closed.")
    remote.setRunning(False)


MAIN_WINDOW.setInputInterface(inputInterface)
MAIN_WINDOW.addWidget(homeScreen)
MAIN_WINDOW.addWidget(webInterface)

keyboard.setInputInterface(inputInterface)
remote.setInputInterface(inputInterface)
MAIN_WINDOW.setKeyboard(keyboard)

MAIN_WINDOW.setTab(homeScreen)
MAIN_WINDOW.show()

print("Running main event loop...")
asyncio.run(main())
print("Exiting...")