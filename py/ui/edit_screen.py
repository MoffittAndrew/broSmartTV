print("Importing edit screen...")

from ui.gui import CustomQWidget

from PyQt5.QtWidgets import QLabel, QVBoxLayout

class EditScreen(CustomQWidget):
    def __init__(self, navBarButton = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setNavBarButton(navBarButton)
        
        self.__heading = QLabel("placeholder")
        self.__heading.setStyleSheet("font-size: 44px; font-weight: bold; color: white;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.__heading)
        self.setLayout(layout)
        
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
    
    def setText(self, text):
        self.__heading.setText(text)

editScreen = EditScreen()