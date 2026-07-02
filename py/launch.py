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

def append_update_log_line(line):
    line = str(line).strip()
    if not line:
        return

    print(line)

    launch_screen = globals().get("LAUNCH_SCREEN")
    if launch_screen is not None:
        launch_screen.append_log_line(line)

def init_qt():
    """Initialize the minimal launch UI shown before main.py is ready."""
    global APP, LAUNCH_SCREEN
    
    from globals import DISPLAY
    
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from ui.launch_screen import LaunchScreen

    APP = QApplication([])

    # Hide mouse pointer
    APP.setOverrideCursor(Qt.CursorShape.BlankCursor)

    LAUNCH_SCREEN = LaunchScreen(display=DISPLAY, log_font_size=30, log_max_lines=15)

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
    
    LAUNCH_SCREEN.stop()
    LAUNCH_SCREEN.hide()

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


async def shutdown_background_tasks(tasks):
    """Cancel/await launcher background tasks before process exit."""
    remoteInterface.setRunning(False)

    pending = []
    for task in tasks:
        if task is None or task.done():
            continue
        task.cancel()
        pending.append(task)

    if not pending:
        return

    try:
        await asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=2)
    except asyncio.TimeoutError:
        print("Timed out while shutting down background tasks.")


def main():
    """Top-level launcher orchestration for Pi runtime."""
    try:
        # Wait for the remote to connect
        asyncio.run(awaitFindRemote())
        with qtinter.using_asyncio_from_qt():
            # Switch projector on
            projector_task = asyncio.create_task(projector_on())
            remote_task = asyncio.create_task(remoteInterface.connect())

            init_qt()
            
            # Run the update script, then launch smart TV
            print("Starting launch screen...")
            LAUNCH_SCREEN.show()
            update_task = asyncio.create_task(updateThenLaunch())
            APP.exec_()
            print("App closed.")

            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                shutdown_background_tasks([projector_task, remote_task, update_task])
            )

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