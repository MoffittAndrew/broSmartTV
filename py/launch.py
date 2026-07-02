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
_update_log_lines = []
_update_log_max_lines = 5


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


def append_update_log_line(line):
    global _update_log_lines

    line = str(line).strip()
    if not line:
        return

    print(line)
    _update_log_lines.append(line)
    _update_log_lines = _update_log_lines[-_update_log_max_lines:]

    label = globals().get("update_log_label")
    if label is not None:
        label.setText("\n".join(_update_log_lines))

def init_qt():
    """Initialize the minimal launch UI shown before main.py is ready."""
    global APP, LAUNCH_FRAME, waiting_circ, update_log_label, _update_log_lines
    
    from globals import DISPLAY
    
    # PyQt imports
    from PyQt5.QtWidgets import QApplication, QWidget, QLabel
    from PyQt5.QtCore import Qt, QSize
    from PyQt5.QtGui import QFont
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

    # Show rolling update output below the spinner for quick on-device debugging.
    _update_log_lines = []
    update_log_label = QLabel(LAUNCH_FRAME)
    update_log_label.setWordWrap(True)
    update_log_label.setStyleSheet("color: white;")
    font = QFont("Monospace")
    font.setStyleHint(QFont.TypeWriter)
    update_log_label.setFont(font)

    margin = 40
    label_height = min(220, max(120, DISPLAY.HEIGHT // 3))
    update_log_label.setGeometry(
        margin,
        DISPLAY.HEIGHT - label_height - margin,
        DISPLAY.WIDTH - (2 * margin),
        label_height,
    )
    update_log_label.setText("Waiting for update output...")

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
    append_update_log_line("Running update script...")
    try:
        proc = await asyncio.create_subprocess_exec(
            "update",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        if proc.stdout is not None:
            while True:
                raw_line = await proc.stdout.readline()
                if not raw_line:
                    break
                append_update_log_line(raw_line.decode(errors="replace"))

        return_code = await proc.wait()
        append_update_log_line(f"Update script exited with code {return_code}")
    
    except Exception as e:
        append_update_log_line("The following error occured when attempting to run the update script:")
        append_update_log_line(e)
        append_update_log_line("Skipping update check.")
    
    finally:
        # Load the updated code into memory
        append_update_log_line("Reloading imported modules...")
        import sys
        for mod in reload_modules:
            sys.modules.pop(mod, None)
        append_update_log_line("Reloaded modules.")
    
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