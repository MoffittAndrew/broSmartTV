import asyncio
import qtinter

reload_modules = [
    "globals",
    "interface.projector_interface",
    "interface.ir_interface",
    "interface.remote_interface",
]

def init_qt():
    global APP, LAUNCH_FRAME, waiting_circ
    
    from globals import DISPLAY
    
    # PyQt imports
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import Qt, QSize
    from waiting_spinner import QtWaitingSpinner

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
    
    from interface.projector_interface import projectorInterface
    print("Switching projector on...")
    await projectorInterface.on()

def launch_app():
    
    from interface.remote_interface import remoteInterface
    asyncio.create_task(remoteInterface.init())
    
    print("Launching main program...")
    from main import MAIN_WINDOW
    MAIN_WINDOW.show()
    
    waiting_circ.stop()
    LAUNCH_FRAME.hide()

async def update_then_launch():
    
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
        print("Reloading imported modules...")
        import sys
        for mod in reload_modules:
            sys.modules.pop(mod)
        print("Reloaded modules.")
    
    launch_app()

def launch():
    
    init_qt()
    asyncio.create_task(projector_on())
    
    print("Starting launch screen...")
    LAUNCH_FRAME.show()
    asyncio.create_task(update_then_launch())
    APP.exec_()

async def wait_for_remote():
    
    from interface.remote_interface import remoteInterface
    with qtinter.using_qt_from_asyncio():
        await remoteInterface.await_power_on()

def main():
    
    from interface.remote_interface import remoteInterface
    if remoteInterface.isRunning():
        with qtinter.using_asyncio_from_qt():
            launch()

if __name__ == "__main__":
    print("Starting launch.py...")
    try:
        asyncio.run(wait_for_remote())
        main()
        
        print("Waiting for remote loop to shut down...")
        from interface.remote_interface import remoteInterface
        from globals import REMOTE
        remoteInterface.setRunning(False)
        asyncio.run(asyncio.sleep(REMOTE.CHECK_ALIVE_INTERVAL))
        
    except KeyboardInterrupt:
        print("Launch script manually cancelled by user")
        exit(130)
    print("Exiting launch.py...")