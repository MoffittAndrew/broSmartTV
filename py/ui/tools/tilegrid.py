# Sets up a grid of tiles (for the home screen)

print("Importing tile grid...")

from globals import GUI
from ui.tools.tiles import tiles
from ui.gui import CustomQWidget

from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import Qt

class TileGrid(CustomQWidget):
    def __init__(self, columns:int = GUI.TILEGRID.COLUMNS, tiles:list = tiles, navBarButton = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setColumns(columns)
        self.setTiles(tiles)
        self.setNavBarButton(navBarButton)
    
    ## Getters
    
    def getColumns(self):
        return self.__columns
    
    def getTiles(self):
        return self.__tiles
    
    def getNavBarButton(self):
        return self.__navBarButton
    
    def getPrimaryButton(self):
        if len(self.getTiles()[0]) > 0:
            return self.getTiles()[0][0]
        else:
            return None
    
    ## Setters
    
    def setColumns(self, columns):
        self.__columns = columns
    
    def setTiles(self, tilesList: list):
        
        self.__tilesList = tilesList
        self.__tiles = []
        row = []
        counter = 0
        for i in range(len(self.__tilesList)):
            if counter < self.getColumns():
                row.append(self.__tilesList[i])
            else:
                self.__tiles.append(row)
                row = []
                counter = 0
            counter += 1
        self.__tiles.append(row)
        
        tiles = self.getTiles()
        for i_row in range(len(tiles)):
            if len(tiles[i_row]) > 0:
                for i_col in range(len(tiles[i_row]) - 1):
                    tiles[i_row][i_col + 1].setNavLeft(tiles[i_row][i_col])
                    tiles[i_row][i_col].setNavRight(tiles[i_row][i_col + 1])
        
        if len(tiles) > 0:
            for i_row in range(len(tiles) - 1):
                for i_col in range(len(tiles[i_row])):
                    if i_col < len(tiles[i_row + 1]):
                        lowerButton = tiles[i_row + 1][i_col]
                        lowerButton.setNavUp(tiles[i_row][i_col])
                    else:
                        lowerButton = tiles[i_row + 1][-1]
                    
                    tiles[i_row][i_col].setNavDown(lowerButton)
        
        layout = QGridLayout()
        layout.setOriginCorner(Qt.TopLeftCorner)
        layout.setContentsMargins(0, 0, 0, 0)
        for i_row in range(len(tiles)):
            for i_col in range(len(tiles[i_row])):
                tile = tiles[i_row][i_col]
                layout.addWidget(tile, i_row, i_col)
        
        self.setFixedWidth(len(self.getTiles()[0]) * GUI.TILE.WIDTH)
        self.setFixedHeight(len(self.getTiles()) * GUI.TILE.HEIGHT)
        self.setLayout(layout)
    
    def setNavBarButton(self, navBarButton):
        self.__navBarButton = navBarButton
        if navBarButton is not None:
            tiles = self.getTiles()
            for tile in tiles[0]:
                tile.setNavUp(navBarButton)

tileGrid = TileGrid()