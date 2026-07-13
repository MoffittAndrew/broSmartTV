# Sets up a grid of tiles (for the home screen)

print("Importing tile grid...")

from globals import GUI
from ui.tools.tiles import tiles
from ui.tools.section import GridSection

class TileGrid(GridSection):
    def __init__(self, columns:int = GUI.TILEGRID.COLUMNS, tiles:list = tiles, navBarButton = None, *args, **kwargs):
        super().__init__(columns=columns, widgets=[], spacing=GUI.SPACING.TIGHT, edgePolicy="last", *args, **kwargs)

        self.__tilesList = []
        self.__navBarButton = None
        self.setTiles(tiles)
        self.setNavBarButton(navBarButton)
    
    ## Getters
    
    def getColumns(self):
        return super().getColumns()
    
    def getTiles(self):
        return self.getRows()
    
    def getNavBarButton(self):
        return self.__navBarButton
    
    def getPrimaryButton(self):
        return super().getPrimaryButton()
    
    ## Setters
    
    def setColumns(self, columns):
        super().setColumns(columns)
    
    def setTiles(self, tilesList: list):
        self.__tilesList = list(tilesList)
        super().setWidgets(self.__tilesList)

        navBarButton = self.getNavBarButton()
        if navBarButton is not None:
            self.setNavBarButton(navBarButton)
    
    def setNavBarButton(self, navBarButton):
        self.__navBarButton = navBarButton
        if navBarButton is not None:
            tiles = self.getTiles()
            if len(tiles) > 0:
                for tile in tiles[0]:
                    tile.setNavUp(navBarButton)

tileGrid = TileGrid()