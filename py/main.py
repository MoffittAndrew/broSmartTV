# This is the script that runs when the smart TV is powered on (see launch.py)
# Can also be run from a PC for development and testing purposes (although the
# GUI doesn't render quite right when not run on the raspberry pi)

print("Starting...")

from PyQt5.QtWidgets import QApplication

APP = QApplication.instance()
if APP is None:
    APP = QApplication([])

print("Starting imports...")
from ui.gui import MAIN_WINDOW, ScreenCastView
from interface.input_interface import inputInterface
#from interface.web_interface import webInterface
from interface.remote_interface import remoteInterface
from interface.keyboard_interface import keyboardInterface
from interface.projector_interface import projectorInterface
from screen_cast import (
    startScreenCastServer,
    setFrameHandler,
    setConnectionHandler,
    setDisconnectHandler,
)
from teardown import reset_shutdown_state, teardown_app
from ui.home import homeScreen

import asyncio
import qtinter
print("Completed imports.")


def request_shutdown():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop_policy().get_event_loop()

    if loop.is_running():
        loop.create_task(teardown_app(projector_interface=projectorInterface, quit_app=False))
    else:
        loop.run_until_complete(teardown_app(projector_interface=projectorInterface, quit_app=False))

# NOTE - this only runs when launching the script directly (i.e. from a PC)
# When running on the pi, we just import MAIN_WINDOW from launch.py
def main():
    with qtinter.using_asyncio_from_qt():  # enable asyncio in qt code
        reset_shutdown_state()
        asyncio.create_task(remoteInterface.connect())
        print("Starting GUI...")
        MAIN_WINDOW.show()
        print("Starting screen cast server...")
        asyncio.create_task(startScreenCastServer())
        APP.aboutToQuit.connect(request_shutdown)
        APP.exec_()
        print("App closed.")

# set up interface relationships
MAIN_WINDOW.setInputInterface(inputInterface)
MAIN_WINDOW.addWidget(homeScreen)
#MAIN_WINDOW.addWidget(webInterface)

inputInterface.setProjectorInterface(projectorInterface)
keyboardInterface.setInputInterface(inputInterface)
remoteInterface.setInputInterface(inputInterface)
MAIN_WINDOW.setKeyboard(keyboardInterface)

MAIN_WINDOW.setDefaultTab(homeScreen)

screenCastView = ScreenCastView(MAIN_WINDOW)
MAIN_WINDOW.setScreenCastWidget(screenCastView)
setFrameHandler(screenCastView.setFrame)
setConnectionHandler(MAIN_WINDOW.showScreenCast)
setDisconnectHandler(MAIN_WINDOW.hideScreenCast)

if __name__ == "__main__":
    print("Running main event loop...")
    main()
    print("Exiting...")