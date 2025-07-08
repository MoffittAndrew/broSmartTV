print("Starting launch.py...")

import asyncio
import qtinter
import sys

# PyQt imports
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QSize
from waiting_spinner import QtWaitingSpinner

WIDTH = 1920
HEIGHT = 1080
APP = QApplication([])

# Hide mouse pointer
APP.setOverrideCursor(Qt.CursorShape.BlankCursor)

# Initialize window
LAUNCH_FRAME = QWidget()
LAUNCH_FRAME.setWindowTitle("Launching...")
LAUNCH_FRAME.setFixedSize(QSize(WIDTH, HEIGHT))
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

def projector_on():
    
    print("Switching projector on...")
    from projector_interface import projectorInterface
    projectorInterface.on()

def launch():
    
    print("Launching main program...")
    from main import MAIN_WINDOW, remote
    MAIN_WINDOW.show()
    
    waiting_circ.stop()
    LAUNCH_FRAME.hide()
    
    asyncio.create_task(remote.init())

async def update():
    
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
        sys.modules.pop('projector_interface')
        print("Reloaded modules.")
        
        launch()

def main():
    with qtinter.using_asyncio_from_qt():
        
        projector_on()
        
        print("Starting launch screen...")
        LAUNCH_FRAME.show()
        asyncio.create_task(update())
        APP.exec_()

main()
print("Exiting launch.py...")