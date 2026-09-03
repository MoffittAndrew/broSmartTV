print("Importing soundbar interface...")

# Normally shouldn't cross-import interfaces, but making (another) exception here for code simplicity
from interface.ir_interface import irInterface
from globals import SOUNDBAR

from asyncio import sleep

class SoundbarInterface:
    def __init__(self, irInterface = None, *args, **kwargs):
        self.setIrInterface(irInterface)
    
    def setIrInterface(self, irInterface):
        self.__irInterface = irInterface
    
    def getIrInterface(self):
        return self.__irInterface
    
    async def send(self, data):
        if self.getIrInterface() is not None:
            self.getIrInterface().send(SOUNDBAR.DEVICE_NAME, data)
            await sleep(SOUNDBAR.INPUT_DELAY)
        else:
            print("Cannot send IR data, no IR interface has been set!")
    
    async def power(self):
        await self.send(SOUNDBAR.CODES.POWER)
    
    async def off(self):
        # for now
        #await self.send(SOUNDBAR.CODES.OFF)
        ...
    
    async def mute(self):
        await self.send(SOUNDBAR.CODES.MUTE)
    
    async def volUp(self):
        await self.send(SOUNDBAR.CODES.VOL_UP)
    
    async def volDown(self):
        await self.send(SOUNDBAR.CODES.VOL_DOWN)
    
    async def trebleUp(self):
            await self.send(SOUNDBAR.CODES.TREBLE_UP)
        
    async def trebleDown(self):
        await self.send(SOUNDBAR.CODES.TREBLE_DOWN)
    
    async def bassUp(self):
        await self.send(SOUNDBAR.CODES.BASS_UP)
    
    async def bassDown(self):
        await self.send(SOUNDBAR.CODES.BASS_DOWN)
    
    async def switchInputChannel(self, inputChannel):
        await self.send(SOUNDBAR.CODES.SRC_ + inputChannel)
        await sleep(SOUNDBAR.CHANNEL_SWITCH_DELAY)
    
    async def switchMode(self, mode):
        await self.send(SOUNDBAR.CODES.MODE_ + mode)

soundbarInterface = SoundbarInterface(irInterface=irInterface)