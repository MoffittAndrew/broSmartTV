print("Importing projector interface...")

# Normally shouldn't cross-import interfaces, but making an exception here for code simplicity
from interface.ir_interface import irInterface
from globals import PROJECTOR

from asyncio import sleep

class ProjectorInterface:
    def __init__(self, irInterface = None, *args, **kwargs):
        self.setIrInterface(irInterface)
    
    def setIrInterface(self, irInterface):
        self.__irInterface = irInterface
    
    def getIrInterface(self):
        return self.__irInterface
    
    async def send(self, data):
        if self.getIrInterface() is not None:
            self.getIrInterface().send(PROJECTOR.DEVICE_NAME, data)
            await sleep(PROJECTOR.INPUT_DELAY)
        else:
            print("Cannot send IR data, no IR interface has been set!")
    
    async def on(self):
        await self.send(PROJECTOR.CODES.ON)
        await self.send(PROJECTOR.CODES.RETURN)
    
    async def off(self):
        # for now
        #await self.send(PROJECTOR.CODES.OFF)
        ...
    
    async def select(self):
        await self.send(PROJECTOR.CODES.SELECT)
    
    async def navUp(self):
        await self.send(PROJECTOR.CODES.NAV_UP)
    
    async def navRight(self):
        await self.send(PROJECTOR.CODES.NAV_RIGHT)
    
    async def navDown(self):
        await self.send(PROJECTOR.CODES.NAV_DOWN)
    
    async def navLeft(self):
        await self.send(PROJECTOR.CODES.NAV_LEFT)
    
    async def back(self):
        await self.send(PROJECTOR.CODES.RETURN)
    
    async def menu(self):
        await self.send(PROJECTOR.CODES.MENU)
    
    async def volUp(self):
        await self.send(PROJECTOR.CODES.VOL_UP)
    
    async def volDown(self):
        await self.send(PROJECTOR.CODES.VOL_DOWN)
    
    async def switchInputChannel(self, inputChannel):
        if inputChannel == PROJECTOR.CHANNELS.VGA:
            await self.send(PROJECTOR.CODES.SRC_ + inputChannel)
        elif inputChannel == PROJECTOR.CHANNELS.COMPONENT:
            ...
        else: # Default to HDMI
            await self.send(PROJECTOR.CODES.SRC_ + PROJECTOR.CHANNELS.VGA)
            await sleep(PROJECTOR.INPUT_DELAY)
            await self.send(PROJECTOR.CODES.SRC_ + PROJECTOR.CHANNELS.SEARCH)
        
        await sleep(PROJECTOR.CHANNEL_SWITCH_DELAY)

projectorInterface = ProjectorInterface(irInterface=irInterface)