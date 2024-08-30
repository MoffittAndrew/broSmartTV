from gui import APP
from tiles import tiles
from input_interface import inputInterface
from home import homeScreen
from remote import remote

inputInterface.setSelectedButton(tiles[0])

homeScreen.show()
remote.setInputInterface(inputInterface)
remote.init()

APP.exec_()