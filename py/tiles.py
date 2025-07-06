print("Importing tiles...")

from globals import PATH
from tile import Tile, DeviceTile, WebTile

from os import listdir
from os.path import isfile, join


def _sortTiles(tiles):
    
    # insertion sort by index
    for i in range(1, len(tiles)):
        currentTile = tiles[i]
        pos = i
        while pos > 0 and tiles[pos - 1].getIndex() > currentTile.getIndex():
            tiles[pos] = tiles[pos - 1]
            pos -= 1
        tiles[pos] = currentTile
    
    return tiles


def _getTilesFromPath(path, TileType):
    
    tiles = []
    tileFiles = [f for f in listdir(path) if isfile(join(path, f))]
    for file in tileFiles:
        filepath = path + file
        kwargs = {"filepath": filepath}
        
        tileFile = open(filepath)
        lines = tileFile.readlines()
        tileFile.close()
        
        for line in lines:
            datapair = line.split("=", 1)
            key = datapair[0].strip()
            value = datapair[1].strip()
            kwargs[key] = value
        
        tile = TileType(**kwargs)
        tiles.append(tile)
    
    return tiles


def _saveTile(tile):
    
    lines = []
    tileAttrs = tile.getAllAttrs()
    for key in tileAttrs:
        lines.append(f"{key}={tileAttrs[key]}")
    
    tileFile = open(tile.getFilepath(), 'w')
    tileFile.write('\n'.join(lines))
    tileFile.close()


def _readTiles():
    
    print("Reading tiles...")
    
    tiles = []
    path = PATH + "tiles\\"
    tiles += _getTilesFromPath(path, Tile)
    tiles += _getTilesFromPath(path + "device\\", DeviceTile)
    tiles += _getTilesFromPath(path + "web\\", WebTile)
    
    print("Successfully read tiles.")
    
    return _sortTiles(tiles)


def saveTiles(tiles):
    
    print("Saving tiles...")
    
    for tile in tiles:
        _saveTile(tile)
    
    print("Successfully saved tiles.")

tiles = _readTiles()