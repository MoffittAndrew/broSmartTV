"""Launcher entrypoint used on the Raspberry Pi.

Startup flow when running this file directly:
1. Host the lightweight standby webpage and race it against remote
   discovery - whichever wakes the app first (web "turn bro on" button or
   remote found) wins. QApplication/init_qt() is deliberately not created
   until this resolves, so the box stays low memory/power while off.
2. Start a lightweight launch screen (spinner).
3. Power on the projector and keep remote connection alive.
4. Run the update script.
5. Import main.py and show the main UI (this also starts the full screen
   cast server, replacing the standby webpage at the same URL).

Any fatal startup/task error exits the process with code 1 so the outer
bash launch loop can automatically restart the app.
"""

import asyncio
import os
import sys
import qtinter

from app_logging import get_adapter

from interface.remote_interface import remoteInterface
from launcher_lock import acquire_launch_lock, release_launch_lock, LaunchAlreadyRunningError
from webserver.standby_server import start_standby_server, stop_standby_server


logger = get_adapter("launcher", "startup")

reload_modules = [
    "globals",
    "interface.projector_interface",
    "interface.ir_interface",
    #"interface.remote_interface", don't reload this, it will break the remote connection
]

_restart_requested = False
EXIT_ALREADY_RUNNING = 200


def request_restart(reason, exc=None):
    """Force a hard process exit so the outer launcher can restart us."""
    global _restart_requested
    if _restart_requested:
        return

    _restart_requested = True
    logger.error(f"Fatal error: {reason}")
    if exc is not None:
        logger.error(
            "Launcher exception",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
        )

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

    logger.info(line, category="update")


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
    logger.info("Switching projector on...", category="projector")
    await projectorInterface.on()


def launch():
    """Import main.py and transition from launch screen to the full UI."""
    logger.info("Launching main program...")
    from main import MAIN_WINDOW
    from webserver.screen_cast import startScreenCastServer
    MAIN_WINDOW.show()
    
    LAUNCH_SCREEN.stop()
    LAUNCH_SCREEN.hide()
    
    logger.info("Starting screen cast server...", category="screencast")
    asyncio.create_task(start_screen_cast_server(startScreenCastServer))


async def start_screen_cast_server(start_server):
    """Escalate Pi server startup failures to the restart-owning launcher."""
    try:
        await start_server()
    except Exception as exc:
        request_restart("Failed to start screen cast server", exc)

async def updateThenLaunch():
    """Run updater, reload selected modules, then launch main."""
    from globals import DEVICE

    # Run the update script to pull code changes from github
    if DEVICE.IS_RASPBERRY_PI:
        append_update_log_line("Running update script...")
        try:
            update_script = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "launcher", "update")
            )
            proc = await asyncio.create_subprocess_exec(
                "/bin/bash",
                update_script,
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
    
    else:
        append_update_log_line("Skipping update script on non-Raspberry Pi device.")
    
    # Launch the smart TV
    try:
        launch()
    except Exception as e:
        request_restart("Failed to launch main program", e)

async def awaitFindRemote():
    """Block until the remote is found before showing launch UI."""
    with qtinter.using_qt_from_asyncio():
        await remoteInterface.awaitFindRemote()


async def off_phase():
    """Host the standby webpage and race it against remote discovery.

    Whichever wakes the app first wins; the loser's work is simply
    abandoned (the remote-scan task is cancelled if the web button wins -
    remoteInterface.connect(), called later regardless of trigger, already
    re-scans for the remote if it hasn't been found yet, so nothing is lost
    and the remote can still be paired/connected normally afterward).
    """
    wake_event = asyncio.Event()

    async def find_remote_and_wake():
        await awaitFindRemote()
        wake_event.set()

    await start_standby_server(wake_event)
    remote_task = asyncio.create_task(find_remote_and_wake())

    await wake_event.wait()

    await stop_standby_server()

    if not remote_task.done():
        remote_task.cancel()
        try:
            await remote_task
        except asyncio.CancelledError:
            pass


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
        logger.warning("Timed out while shutting down background tasks.", category="teardown")


def main():
    """Top-level launcher orchestration for Pi runtime."""
    launch_lock_handle = None
    try:
        launch_lock_handle = acquire_launch_lock()

        # Host the standby webpage and wait for either the remote or the web button to wake us
        asyncio.run(off_phase())
        with qtinter.using_asyncio_from_qt():
            # Switch projector on
            projector_task = asyncio.create_task(projector_on())
            remote_task = asyncio.create_task(remoteInterface.connect())

            init_qt()
            
            # Run the update script, then launch smart TV
            logger.info("Starting launch screen...")
            LAUNCH_SCREEN.show()
            update_task = asyncio.create_task(updateThenLaunch())
            APP.exec_()
            logger.info("App closed.", category="teardown")

            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(
                    shutdown_background_tasks([projector_task, remote_task, update_task])
                )
            else:
                loop.run_until_complete(
                    shutdown_background_tasks([projector_task, remote_task, update_task])
                )

    except LaunchAlreadyRunningError as e:
        logger.error(str(e))
        exit(EXIT_ALREADY_RUNNING)
    except KeyboardInterrupt:
        logger.warning("Launch script manually cancelled by user", category="teardown")
        exit(130)
    except Exception as e:
        request_restart("Launcher crashed unexpectedly", e)
    finally:
        release_launch_lock(launch_lock_handle)

if __name__ == "__main__":
    logger.info("Starting launch.py...")
    main()
    logger.info("Exiting launch.py...", category="teardown")