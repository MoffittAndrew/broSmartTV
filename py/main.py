"""Main application entrypoint.

There are two startup paths:
1. Raspberry Pi runtime: launch.py imports this module, which executes module
    setup below (UI wiring, interfaces, screencast callbacks). launch.py then
    shows MAIN_WINDOW.
2. Local development/runtime testing: this file is run directly, so __main__
    calls main(), which starts remote connection + screencast server and enters
    the Qt event loop.
"""

print("Starting...")

from PyQt5.QtWidgets import QApplication
from typing import cast

app_instance = QApplication.instance()
if app_instance is None:
    app_instance = QApplication([])
APP = cast(QApplication, app_instance)

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
    """Run async teardown whether Qt quit comes from running loop or not."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    if loop.is_running():
        loop.create_task(teardown_app(projector_interface=projectorInterface, quit_app=False))
    else:
        loop.run_until_complete(teardown_app(projector_interface=projectorInterface, quit_app=False))


async def start_screen_cast_server():
    """Report direct-run server startup failures and close through shared teardown."""
    try:
        await startScreenCastServer()
    except Exception as exc:
        print(f"Failed to start screen cast server: {exc}")
        await teardown_app(projector_interface=projectorInterface, quit_app=True)

# NOTE - this only runs when launching the script directly (i.e. from a PC)
# When running on the pi, we just import MAIN_WINDOW from launch.py
def main():
    """Start services and run Qt loop for direct main.py execution."""
    with qtinter.using_asyncio_from_qt():  # enable asyncio in qt code
        reset_shutdown_state()
        asyncio.create_task(remoteInterface.connect())
        print("Starting GUI...")
        MAIN_WINDOW.show()
        print("Starting screen cast server...")
        asyncio.create_task(start_screen_cast_server())
        APP.aboutToQuit.connect(request_shutdown)
        APP.exec_()
        print("App closed.")

# Module-level setup that runs on import (used by both startup paths):
# - link interfaces together
# - attach widgets/callbacks
# - configure screencast display handlers
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