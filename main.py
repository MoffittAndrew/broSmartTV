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
    #asyncio.create_task(remote.init())
    print("Starting GUI...")
    APP.exec_()
    remote.setRunning(False)


MAIN_WINDOW.addWidget(homeScreen)
MAIN_WINDOW.addWidget(webInterface)

inputInterface.setParent(MAIN_WINDOW)
inputInterface.setSelectedButton(homeScreen.getPrimaryButton())
keyboard.setInputInterface(inputInterface)
remote.setInputInterface(inputInterface)
MAIN_WINDOW.setKeyboard(keyboard)

MAIN_WINDOW.show()

print("Running main event loop...")
asyncio.run(main())
print("Exiting...")