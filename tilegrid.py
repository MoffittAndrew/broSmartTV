from globals import TILEGRID
from tiles import tiles

from PyQt5.QtWidgets import QWidget, QGridLayout

class TileGrid(QWidget):
    def __init__(this, columns:int = TILEGRID.COLUMNS, tiles:list = tiles, navBarButton = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.setColumns(columns)
        this.setTiles(tiles)
        this.setNavBarButton(navBarButton)
        
    ## Getters
    
    def getColumns(this):
        return this.__columns
    
    def getTiles(this):
        return this.__tiles
    
    def getNavBarButton(this):
        return this.__navBarButton
    
    def getPrimaryButton(this):
        return this.getTiles()[0][0]
    
    ## Setters
    
    def setColumns(this, columns):
        this.__columns = columns
    
    def setTiles(this, tiles_list):
        
        this.__tiles = []
        row = []
        counter = 0
        for i in range(len(tiles_list)):
            if counter < this.getColumns():
                row.append(tiles_list[i])
            else:
                this.__tiles.append(row)
                row = []
                counter = 0
            counter += 1
        this.__tiles.append(row)
        
        tiles = this.getTiles()
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
        for i_row in range(len(tiles)):
            for i_col in range(len(tiles[i_row])):
                tile = tiles[i_row][i_col]
                layout.addWidget(tile, i_row, i_col)
        
        this.setLayout(layout)
        
    def setNavBarButton(this, navBarButton):
        this.__navBarButton = navBarButton
        if navBarButton != None:
            tiles = this.getTiles()
            for tile in tiles[0]:
                tile.setNavUp(navBarButton)

tileGrid = TileGrid()