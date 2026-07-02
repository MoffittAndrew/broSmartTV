"""Launcher entrypoint used on the Raspberry Pi.

Startup flow when running this file directly:
1. Wait for the remote to be discoverable.
2. Start a lightweight launch screen (spinner).
3. Power on the projector and keep remote connection alive.
4. Run the update script.
5. Import main.py and show the main UI.

Any fatal startup/task error exits the process with code 1 so the outer
bash launch loop can automatically restart the app.
"""

import asyncio
import os
import sys
import traceback
import qtinter

from interface.remote_interface import remoteInterface

reload_modules = [
    "globals",
    "interface.projector_interface",
    "interface.ir_interface",
    #"interface.remote_interface",
]

_restart_requested = False


def request_restart(reason, exc=None):
    """Force a hard process exit so the outer launcher can restart us."""
    global _restart_requested
    if _restart_requested:
        return

    _restart_requested = True
    print(f"Fatal error: {reason}")
    if exc is not None:
        traceback.print_exception(type(exc), exc, exc.__traceback__)

    app = globals().get("APP")
    if app is not None:
        app.exit(1)

    # Ensure the launcher process exits so the outer bash loop can restart it.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)


def create_monitored_task(coro, name):
    """Create a task that escalates unhandled exceptions to process restart."""
    task = asyncio.create_task(coro, name=name)

    def _task_done_callback(done_task):
        if done_task.cancelled():
            return

        exc = done_task.exception()
        if exc is not None:
            request_restart(f"Task '{name}' crashed", exc)

    task.add_done_callback(_task_done_callback)
    return task

def init_qt():
    """Initialize the minimal launch UI shown before main.py is ready."""
    global APP, LAUNCH_FRAME, waiting_circ
    
    from globals import DISPLAY
    
    # PyQt imports
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import Qt, QSize
    from ui.waiting_spinner import QtWaitingSpinner

    APP = QApplication([])

    # Hide mouse pointer
    APP.setOverrideCursor(Qt.CursorShape.BlankCursor)

    # Initialize window
    LAUNCH_FRAME = QWidget()
    LAUNCH_FRAME.setWindowTitle("Launching...")
    LAUNCH_FRAME.setFixedSize(QSize(DISPLAY.WIDTH, DISPLAY.HEIGHT))
    LAUNCH_FRAME.setContentsMargins(0, 0, 0, 0)

    # Set background color
    LAUNCH_FRAME.setAutoFillBackground(True)
    p = LAUNCH_FRAME.palette()
    p.setColor(LAUNCH_FRAME.backgroundRole(), Qt.black)
    LAUNCH_FRAME.setPalette(p)

    # Setup spinning circle
    waiting_circ = QtWaitingSpinner()
    waiting_circ.setParent(LAUNCH_FRAME)
    waiting_circ.start()

async def projector_on():
    """Power on the projector while launch/update work continues."""
    from interface.projector_interface import projectorInterface
    print("Switching projector on...")
    await projectorInterface.on()


def launch():
    """Import main.py and transition from launch screen to the full UI."""
    print("Launching main program...")
    from main import MAIN_WINDOW
    MAIN_WINDOW.show()
    
    waiting_circ.stop()
    LAUNCH_FRAME.hide()

async def updateThenLaunch():
    """Run updater, reload selected modules, then launch main."""
    # Run the update script to pull code changes from github
    print("Running update script...")
    try:
        proc = await asyncio.create_subprocess_exec("update")
        await proc.communicate()
        print("Finished running update script.")
    
    except Exception as e:
        print("The following error occured when attempting to run the update script:")
        print(e)
        print("Skipping update check.")
    
    finally:
        # Load the updated code into memory
        print("Reloading imported modules...")
        import sys
        for mod in reload_modules:
            sys.modules.pop(mod, None)
        print("Reloaded modules.")
    
    # Launch the smart TV
    try:
        launch()
    except Exception as e:
        request_restart("Failed to launch main program", e)

async def awaitFindRemote():
    """Block until the remote is found before showing launch UI."""
    with qtinter.using_qt_from_asyncio():
        await remoteInterface.awaitFindRemote()


def main():
    """Top-level launcher orchestration for Pi runtime."""
    try:
        # Wait for the remote to connect
        asyncio.run(awaitFindRemote())
        with qtinter.using_asyncio_from_qt():
            init_qt()

            # Switch projector on
            create_monitored_task(projector_on(), "projector_on")
            create_monitored_task(remoteInterface.connect(), "remote_connect")
            
            # Run the update script, then launch smart TV
            print("Starting launch screen...")
            LAUNCH_FRAME.show()
            create_monitored_task(updateThenLaunch(), "update_then_launch")
            APP.exec_()
            print("App closed.")

    except KeyboardInterrupt:
        print()
        print("Launch script manually cancelled by user")
        exit(130)
    except Exception as e:
        request_restart("Launcher crashed unexpectedly", e)

if __name__ == "__main__":
    print("Starting launch.py...")
    main()
    print("Exiting launch.py...")