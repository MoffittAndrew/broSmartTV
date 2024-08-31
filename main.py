from gui import APP, MAIN_WINDOW
from input_interface import inputInterface
from home import homeScreen
from remote import remote
from keyboard import keyboard

import asyncio

async def main():
    #asyncio.create_task(remote.init())
    print("Starting GUI...")
    APP.exec_()
    remote.setRunning(False)


inputInterface.setSelectedButton(homeScreen.getPrimaryButton())
keyboard.setInputInterface(inputInterface)
remote.setInputInterface(inputInterface)
MAIN_WINDOW.setKeyboard(keyboard)

MAIN_WINDOW.show()
#homeScreen.show()

asyncio.run(main())