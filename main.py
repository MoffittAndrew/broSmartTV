from gui import APP
from tiles import tiles
from input_interface import inputInterface
from home import homeScreen

inputInterface.setSelectedButton(tiles[0])

homeScreen.show()

print(inputInterface.getSelectedButton().getText())
print(inputInterface.getSelectedButton().getNavDown())
inputInterface.navRight()
print(inputInterface.getSelectedButton().getText())
inputInterface.navRight()
print(inputInterface.getSelectedButton().getText())

APP.exec_()