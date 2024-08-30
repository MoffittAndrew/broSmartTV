from globals import INPUT

class InputInterface:
    def __init__(this, selectedButton = None):
        this.setSelectedButton(selectedButton)
        
    def getSelectedButton(this):
        return this.__selectedButton
    
    def setSelectedButton(this, button):
        this.__selectedButton = button
        
    def select(this):
        this.getSelectedButton().activate()
        
    def navigate(this, index:str = INPUT.NAV_RIGHT):
        this.setSelectedButton(this.getSelectedButton().getNavButton(index))
        
    def navUp(this):
        this.navigate(INPUT.NAV_UP)
        
    def navRight(this):
        this.navigate(INPUT.NAV_RIGHT)
        
    def navDown(this):
        this.navigate(INPUT.NAV_DOWN)
        
    def navLeft(this):
        this.navigate(INPUT.NAV_LEFT)
    
inputInterface = InputInterface()