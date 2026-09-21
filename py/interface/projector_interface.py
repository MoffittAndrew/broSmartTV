print("Importing projector interface...")

# Normally shouldn't cross-import interfaces, but making an exception here for code simplicity
from interface.ir_interface import irInterface
from globals import PROJECTOR

from asyncio import sleep

class ProjectorInterface:
    def __init__(self, irInterface = None, *args, **kwargs):
        self.setIrInterface(irInterface)
        self.__volume = {
            PROJECTOR.CHANNELS.HDMI: 0,
            PROJECTOR.CHANNELS.S_VIDEO: 0,
            PROJECTOR.CHANNELS.COMPONENT: 0,
            PROJECTOR.CHANNELS.VGA: 0,
        }
        self.__srcChannel = PROJECTOR.CHANNELS.HDMI
        self.__activeVideoChannel = PROJECTOR.CHANNELS.HDMI
    
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
        await self.send(PROJECTOR.CODES.OFF)
    
    async def calibrateVolume(self, volume=0):
        self.__volume[PROJECTOR.CHANNELS.HDMI] = 10
        await self.setVolume(0)
        await self.setVolume(volume)
    
    async def setVolume(self, volume, channel=None):
        if channel is None:
            channel = self.__srcChannel
        while self.__volume[channel] < volume:
            await self.volUp(channel=channel)
        while self.__volume[channel] > volume:
            await self.volDown(channel=channel)
    
    async def volumeInit(self):
        await self.calibrateVolume()
        await self.setVolume(PROJECTOR.AUTO_VOL_SET)
    
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
    
    async def volUp(self, channel=None):
        await self.send(PROJECTOR.CODES.VOL_UP)
        if channel is None:
            channel = self.__srcChannel
        self.__volume[channel] += 1
        if self.__volume[channel] > 10:
            self.__volume[channel] = 10
    
    async def volDown(self, channel=None):
        await self.send(PROJECTOR.CODES.VOL_DOWN)
        if channel is None:
            channel = self.__srcChannel
        self.__volume[channel] -= 1
        if self.__volume[channel] < 0:
            self.__volume[channel] = 0
    
    async def cycleVideoChannel(self):
        # Cycle through video input channels in the order: HDMI -> S-Video -> Component -> HDMI
        if self.__activeVideoChannel == PROJECTOR.CHANNELS.HDMI:
            self.__activeVideoChannel = PROJECTOR.CHANNELS.S_VIDEO
        elif self.__activeVideoChannel == PROJECTOR.CHANNELS.S_VIDEO:
            self.__activeVideoChannel = PROJECTOR.CHANNELS.COMPONENT
        elif self.__activeVideoChannel == PROJECTOR.CHANNELS.COMPONENT:
            self.__activeVideoChannel = PROJECTOR.CHANNELS.HDMI
        
        await self.send(PROJECTOR.CODES.SRC_ + PROJECTOR.CHANNELS.VIDEO)
        await sleep(PROJECTOR.CHANNEL_SWITCH_DELAY)
        
    async def switchInputChannel(self, inputChannel=PROJECTOR.CHANNELS.HDMI):
        
        if inputChannel == PROJECTOR.CHANNELS.VGA:
            await self.send(PROJECTOR.CODES.SRC_ + inputChannel)
            await sleep(PROJECTOR.CHANNEL_SWITCH_DELAY)
            await self.setVolume(10, channel=inputChannel)
        
        else:
            # input channel must be either HDMI or Component
            if self.__srcChannel == PROJECTOR.CHANNELS.VGA:
                await self.send(PROJECTOR.CODES.SRC_ + PROJECTOR.CHANNELS.VIDEO)
                await sleep(PROJECTOR.CHANNEL_SWITCH_DELAY)
            while self.__activeVideoChannel != inputChannel:
                await self.cycleVideoChannel()
            
            if inputChannel == PROJECTOR.CHANNELS.COMPONENT:
                await sleep(PROJECTOR.CHANNEL_SWITCH_DELAY)
                await self.setVolume(10, channel=inputChannel)
        
        self.__srcChannel = inputChannel

projectorInterface = ProjectorInterface(irInterface=irInterface)