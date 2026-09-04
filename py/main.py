"""Main application entrypoint.

There are two startup paths:
1. Raspberry Pi runtime: launch.py imports this module, which executes module
    setup below (UI wiring, interfaces, screencast callbacks). launch.py then
    shows MAIN_WINDOW.
2. Local development/runtime testing: this file is run directly, so __main__
    calls main(), which starts remote connection + screencast server and enters
    the Qt event loop.
"""

from app_logging import get_adapter

logger = get_adapter("main", "startup")
logger.info("Starting...")

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from typing import cast

from globals import WEB, BIBLE_VERSE

# Must be set before interface.web_interface (imported below) pulls in QtWebEngineWidgets, or
# Chromium never opens the CDP port. A bare port number makes Qt/Chromium bind 127.0.0.1 only;
# webserver/webdebug_routes.py is the only thing allowed to reach it, and only once its own
# token gate passes. Never print WEBDEBUG.TOKEN via `logger` - that feeds the unauthenticated
# /logs page, which would leak the very secret that gates remote code execution in the browser.
os.environ.setdefault("QTWEBENGINE_REMOTE_DEBUGGING", str(WEB.DEBUG.CDP_PORT))
print(f"[webdebug] Available at: https://bro/webdebug?token={WEB.DEBUG.TOKEN}")

# QtWebEngine (used by interface.web_interface) requires this attribute set before any
# QApplication/QCoreApplication instance is constructed, or its import raises ImportError.
if QApplication.instance() is None:
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

app_instance = QApplication.instance()
if app_instance is None:
    app_instance = QApplication([])
APP = cast(QApplication, app_instance)

logger.info("Starting imports...")
from ui.gui import MAIN_WINDOW, ScreenCastView
from interface.input_interface import inputInterface
from interface.web_interface import webInterface
from interface.remote_interface import remoteInterface
from interface.keyboard_interface import keyboardInterface
from interface.projector_interface import projectorInterface
from interface.soundbar_interface import soundbarInterface
from interface.system_interface import systemInterface
from interface.config_interface import configInterface
from interface.bible_interface import bibleInterface
from webserver.screen_cast import (
    startScreenCastServer,
    setFrameHandler,
    setConnectionHandler,
    setDisconnectHandler,
)
from teardown import reset_shutdown_state, teardown_app
from ui.home import homeScreen
from ui.bible_verse_screen import bibleVerseScreen

import asyncio
import qtinter
logger.info("Completed imports.")


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
        logger.exception(
            "Failed to start screen cast server",
            exc,
            category="screencast",
        )
        await teardown_app(projector_interface=projectorInterface, quit_app=True)


async def show_main_window(on_shown=None):
    """Show a random verse screen first if the Bible API is reachable, else go straight home.

    Shared by both startup paths (launch.py's Pi runtime and this module's direct-run main()),
    so the same skip-on-no-internet behavior applies everywhere MAIN_WINDOW is first shown.
    """
    verse = None
    try:
        verse = await asyncio.wait_for(
            bibleInterface.fetch_random_verse(), timeout=BIBLE_VERSE.TOTAL_TIMEOUT_SECONDS
        )
    except Exception as exc:
        logger.warning(f"Timed out waiting for a random verse: {exc}", category="startup")
        verse = None

    if verse is not None:
        bibleVerseScreen.showVerse(verse)
        MAIN_WINDOW.show(initialTab=bibleVerseScreen)
    else:
        MAIN_WINDOW.show()

    if on_shown is not None:
        on_shown()

# NOTE - this only runs when launching the script directly (i.e. from a PC)
# When running on the pi, we just import MAIN_WINDOW from launch.py
def main():
    """Start services and run Qt loop for direct main.py execution."""
    with qtinter.using_asyncio_from_qt():  # enable asyncio in qt code
        reset_shutdown_state()
        asyncio.create_task(remoteInterface.connect())
        logger.info("Starting GUI...", category="gui")

        def _on_shown():
            logger.info("Starting screen cast server...", category="screencast")
            asyncio.create_task(start_screen_cast_server())

        asyncio.create_task(show_main_window(on_shown=_on_shown))
        APP.aboutToQuit.connect(request_shutdown)
        APP.exec_()
        logger.info("App closed.", category="teardown")

# Module-level setup that runs on import (used by both startup paths):
# - link interfaces together
# - attach widgets/callbacks
# - configure screencast display handlers
MAIN_WINDOW.setInputInterface(inputInterface)
MAIN_WINDOW.addWidget(homeScreen)
MAIN_WINDOW.addWidget(webInterface)
webInterface.hide()
MAIN_WINDOW.addWidget(bibleVerseScreen)
bibleVerseScreen.hide()

inputInterface.setProjectorInterface(projectorInterface)
inputInterface.setSoundbarInterface(soundbarInterface)
inputInterface.setSystemInterface(systemInterface)
systemInterface.setProjectorInterface(projectorInterface)
systemInterface.setSoundbarInterface(soundbarInterface)
systemInterface.setConfigInterface(configInterface)
inputInterface.setWebInterface(webInterface)
webInterface.setInputInterface(inputInterface)
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
    logger.info("Running main event loop...")
    main()
    logger.info("Exiting...", category="teardown")