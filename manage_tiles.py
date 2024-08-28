from globals import PATH
from tile import Tile, DeviceTile, WebTile
from os import listdir
from os.path import isfile, join

def getTilesFromPath(path, TileType):
    
    tiles = []
    tile_files = [f for f in listdir(path) if isfile(join(path, f))]
    for file in tile_files:
        kwargs = {}
        
        tile_file = open(path + file)
        lines = tile_file.readlines()
        tile_file.close()
        
        for line in lines:
            datapair = line.split("=", 1)
            key = datapair[0].strip()
            value = datapair[1].strip()
            kwargs[key] = value
        
        tile = TileType(**kwargs)
        tiles.append(tile)
        
    return tiles

def readTiles():
    
    tiles = []
    path = PATH + "tiles\\"
    tiles += getTilesFromPath(path, Tile)
    tiles += getTilesFromPath(path + "device\\", DeviceTile)
    tiles += getTilesFromPath(path + "web\\", WebTile)
    
    return tiles

def writeTiles(tiles):
    
    for tile in tiles:
        return ## TODO