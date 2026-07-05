print("Importing edit screen...")

from ui.gui import CustomQWidget

class EditScreen(CustomQWidget):
    def __init__(self, navBarButton = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setNavBarButton(navBarButton)
        
    ## Getters
    
    def getNavBarButton(self):
        return self.__navBarButton
    
    def getPrimaryButton(self):
        return
    
    ## Setters
        
    def setNavBarButton(self, navBarButton):
        self.__navBarButton = navBarButton
        if navBarButton is not None:
            tiles = self.getTiles()
            for tile in tiles[0]:
                tile.setNavUp(navBarButton)

editScreen = EditScreen()