from manage_tiles import readTiles

tiles = readTiles()

# insertion sort by index
for i in range(1, len(tiles)):
    currentTile = tiles[i]
    pos = i
    while pos > 0 and tiles[pos - 1].getIndex() > currentTile.getIndex():
        tiles[pos] = tiles[pos - 1]
        pos -= 1
    tiles[pos] = currentTile