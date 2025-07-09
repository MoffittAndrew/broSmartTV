print("Importing projector interface...")

# Normally shouldn't cross-import interfaces, but making an exception here for code simplicity
from interface.ir_interface import irInterface

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
        this.send(...)
    
    def off(this):
        this.send(...)
    
    def select(this):
        this.send(...)
    
    def navUp(this):
        this.send(...)
    
    def navRight(this):
        this.send(...)
    
    def navDown(this):
        this.send(...)
    
    def navLeft(this):
        this.send(...)
    
    def back(this):
        this.send(...)

projectorInterface = ProjectorInterface(irInterface=irInterface)