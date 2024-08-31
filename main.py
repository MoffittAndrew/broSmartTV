from gui import APP
from tiles import tiles
from input_interface import inputInterface
from home import homeScreen
from remote import remote

import asyncio


async def main():
    asyncio.create_task(remote.init())
    print("Starting GUI...")
    APP.exec_()
    remote.setRunning(False)
   

inputInterface.setSelectedButton(tiles[0])

homeScreen.show()
remote.setInputInterface(inputInterface)

asyncio.run(main())