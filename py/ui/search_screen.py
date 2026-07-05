print("Importing search screen...")

from ui.gui import CustomQWidget

class SearchScreen(CustomQWidget):
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

searchScreen = SearchScreen()