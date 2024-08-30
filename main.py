from gui import APP
from tiles import tiles
from input_interface import inputInterface
from home import homeScreen

inputInterface.setSelectedButton(tiles[0])

homeScreen.show()

APP.exec_()