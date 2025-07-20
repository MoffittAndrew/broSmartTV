print("Importing projector interface...")

# Normally shouldn't cross-import interfaces, but making an exception here for code simplicity
from interface.ir_interface import irInterface
from globals import PROJECTOR

from asyncio import sleep

class ProjectorInterface:
    def __init__(this, irInterface = None, *args, **kwargs):
        this.setIrInterface(irInterface)
    
    def setIrInterface(this, irInterface):
        this.__irInterface = irInterface
    
    def getIrInterface(this):
        return this.__irInterface
    
    async def send(this, data):
        if this.getIrInterface() is not None:
            this.getIrInterface().send(data)
            await sleep(PROJECTOR.INPUT_DELAY)
        else:
            print("Cannot send IR data, no IR interface has been set!")
    
    async def on(this):
        await this.send(PROJECTOR.CODES.ON)
        await this.send(PROJECTOR.CODES.RETURN)
    
    async def off(this):
        # for now
        #await this.send(PROJECTOR.CODES.OFF)
        ...
    
    async def select(this):
        await this.send(PROJECTOR.CODES.SELECT)
    
    async def navUp(this):
        await this.send(PROJECTOR.CODES.NAV_UP)
    
    async def navRight(this):
        await this.send(PROJECTOR.CODES.NAV_RIGHT)
    
    async def navDown(this):
        await this.send(PROJECTOR.CODES.NAV_DOWN)
    
    async def navLeft(this):
        await this.send(PROJECTOR.CODES.NAV_LEFT)
    
    async def back(this):
        await this.send(PROJECTOR.CODES.RETURN)
    
    async def menu(this):
        await this.send(PROJECTOR.CODES.MENU)
    
    async def volUp(this):
        await this.send(PROJECTOR.CODES.VOL_UP)
    
    async def volDown(this):
        await this.send(PROJECTOR.CODES.VOL_DOWN)
    
    async def switchInputChannel(this, inputChannel):
        if inputChannel == PROJECTOR.CHANNELS.VGA:
            await this.send(PROJECTOR.CODES.SRC_ + inputChannel)
        elif inputChannel == PROJECTOR.CHANNELS.COMPONENT:
            ...
        else: # Default to HDMI
            await this.send(PROJECTOR.CODES.SRC_ + PROJECTOR.CHANNELS.VGA)
            await sleep(PROJECTOR.INPUT_DELAY)
            await this.send(PROJECTOR.CODES.SRC_ + PROJECTOR.CHANNELS.SEARCH)
        
        await sleep(PROJECTOR.CHANNEL_SWITCH_DELAY)

projectorInterface = ProjectorInterface(irInterface=irInterface)