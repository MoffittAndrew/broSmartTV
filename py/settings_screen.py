print("Importing settings screen...")

from PyQt5.QtWidgets import QWidget

class SettingsScreen(QWidget):
    def __init__(this, navBarButton = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.setNavBarButton(navBarButton)
        
    ## Getters
    
    def getNavBarButton(this):
        return this.__navBarButton
    
    def getPrimaryButton(this):
        return
    
    ## Setters
        
    def setNavBarButton(this, navBarButton):
        this.__navBarButton = navBarButton
        if navBarButton != None:
            tiles = this.getTiles()
            for tile in tiles[0]:
                tile.setNavUp(navBarButton)
                
    ## Other
                
    def updateChildPos(this):
        pass

settingsScreen = SettingsScreen()