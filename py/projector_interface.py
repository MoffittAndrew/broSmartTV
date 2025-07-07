print("Importing projector interface...")

import ir

class ProjectorInterface:
    def __init__(this, *args, **kwargs):
        ...
    
    def select(this):
        ir.send(...)
    
    def navUp(this):
        ir.send(...)
    
    def navRight(this):
        ir.send(...)
    
    def navDown(this):
        ir.send(...)
    
    def navLeft(this):
        ir.send(...)
    
    def back(this):
        ir.send(...)

projectorInterface = ProjectorInterface()