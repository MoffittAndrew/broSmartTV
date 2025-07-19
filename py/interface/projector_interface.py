print("Importing projector interface...")

# Normally shouldn't cross-import interfaces, but making an exception here for code simplicity
from interface.ir_interface import irInterface
from globals import IR_CODES
from asyncio import sleep

class ProjectorInterface:
    def __init__(this, irInterface = None, *args, **kwargs):
        this.setIrInterface(irInterface)
    
    def setIrInterface(this, irInterface):
        this.__irInterface = irInterface
    
    def getIrInterface(this):
        return this.__irInterface
    
    def send(this, data):
        if this.getIrInterface() is not None:
            this.getIrInterface().send(data)
        else:
            print("Cannot send IR data, no IR interface has been set!")
    
    def on(this):
        this.send(IR_CODES.ON)
        # Just in case projector is already on
        sleep(0.2)
        this.send(IR_CODES.RETURN)
    
    def off(this):
        this.send(IR_CODES.OFF)
    
    def select(this):
        this.send(IR_CODES.SELECT)
    
    def navUp(this):
        this.send(IR_CODES.NAV_UP)
    
    def navRight(this):
        this.send(IR_CODES.NAV_RIGHT)
    
    def navDown(this):
        this.send(IR_CODES.NAV_DOWN)
    
    def navLeft(this):
        this.send(IR_CODES.NAV_LEFT)
    
    def back(this):
        this.send(IR_CODES.RETURN)
    
    def menu(this):
        this.send(IR_CODES.MENU)
    
    def volUp(this):
        this.send(IR_CODES.VOL_UP)
    
    def volDown(this):
        this.send(IR_CODES.VOL_DOWN)

projectorInterface = ProjectorInterface(irInterface=irInterface)