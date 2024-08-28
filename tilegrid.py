from globals import TILEGRID
from tiles import tiles

from PyQt5 import QtWidgets

class TileGrid(QtWidgets.QWidget):
    def __init__(this, columns:int = TILEGRID.COLUMNS, tiles:list = tiles, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.setColumns(columns)
        this.setTiles(tiles)
        
    ## Getters
    
    def getTiles(this):
        return this.__tiles
    
    ## Setters
    
    def setTiles(this, tiles):
        
        this.__tiles = []
        row = []
        counter = 0
        for i in range(len(tiles)):
            if counter <= 5:
                row.append(tiles[i])
            else:
                this.__tiles.append(row)
                row = []
                counter = 0
            counter += 1
        
        layout = QtWidgets.QGridLayout()
        tiles = this.getTiles()
        
        for i_row in range(len(tiles)):
            for i_col in range(len(tiles[i_row])):
                tile = tiles[i_row][i_col]
                layout.addWidget(tile, i_row, i_col)
        
        this.setLayout(layout)
        
tileGrid = TileGrid()