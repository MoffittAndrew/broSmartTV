# The home screen is made up of a grid of "tiles" (think apple TV layout)
# Each app on the home screen is a tile, which is just a type of Button

print("Importing tile class...")

from globals import TILE
from ui.tools.button import Button#, ToggleButton
from interface.input_interface import inputInterface
#from web_interface import webInterface

class Tile(Button):
    def __init__(
        self,
        index:int = 0,
        name:str = "new tile",
        filepath:str = "",
        *args,
        **kwargs,
    ):
        super().__init__(width = TILE.WIDTH, height = TILE.HEIGHT, *args, **kwargs)
        
        menuOptions = [
            Button(text = TILE.EDIT_NAME_TEXT, callback = self.editName),
            Button(text = TILE.EDIT_IMG_TEXT, callback = self.editImg),
        ]
        for menuOption in menuOptions:
            self.addMenuOption(menuOption)
        
        self.setFilepath(filepath)
        self.setIndex(index)
        self.setName(name)
        self.draw()
        
    ## Getters
    
    def getAllAttrs(self):
        
        attrs = {}
        attrs["index"] = self.getIndex()
        attrs["name"] = self.getName()
        
        return attrs
    
    def getIndex(self):
        return self.__index
    
    def getName(self):
        return self.__name
    
    def getFilepath(self):
        return self.__filepath
    
    ## Setters
    
    def setIndex(self, index):
        if index is not None:
            index = int(index)
        self.__index = index
    
    def setName(self, name):
        self.__name = str(name)
        self.setText(self.getName())
        if self.getFilepath() == "":
            self.setFilepath(self.getName())
        
    def setFilepath(self, filepath):
        self.__filepath = str(filepath).strip().replace(" ", "_")
        
    ## Callbacks
    
    def editName(self):
        return
    
    def editImg(self):
        return


class ProjectorTile(Tile):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        menuOptions = [
        ]
        for menuOption in menuOptions:
            self.addMenuOption(menuOption)
        
        self.setCallback(inputInterface.openProjectorMenu)


class DeviceTile(Tile):
    def __init__(
        self,
        inputChannel:str = "",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        menuOptions = [
            Button(text = TILE.EDIT_INPUT_TEXT, callback = self.editInputChannel),
        ]
        for menuOption in menuOptions:
            self.addMenuOption(menuOption)
        
        self.setInputChannel(inputChannel)
        self.setCallback(self.switchInputChannel)
        
    ## Getters
    
    def getAllAttrs(self):
        
        attrs = super().getAllAttrs()
        attrs["inputChannel"] = self.getInputChannel()
        
        return attrs
    
    def getInputChannel(self):
        return self.__inputChannel
    
    ## Setters
    
    def setInputChannel(self, inputChannel):
        self.__inputChannel = str(inputChannel)
        
    ## Callbacks
    
    async def switchInputChannel(self):
        await inputInterface.switchProjectorInputChannel(self.getInputChannel())
    
    def editInputChannel(self):
        return


"""
class WebTile(Tile):
    def __init__(
        self,
        url:str = "",
        isMusic:bool = False,
        hasSearch:bool = True,
        isPirate:bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        menuOptions = [
            Button(text = TILE.EDIT_URL_TEXT, callback = self.editURL),
            ToggleButton(text = TILE.TOGGLE_MUSIC_TEXT, callback = self.toggleIsMusic),
            ToggleButton(text = TILE.TOGGLE_SEARCH_TEXT, callback = self.toggleHasSearch),
            ToggleButton(text = TILE.TOGGLE_PIRATE_TEXT, callback = self.toggleIsPirate),
        ]
        for menuOption in menuOptions:
            self.addMenuOption(menuOption)
        
        self.setURL(url)
        self.setIsMusic(isMusic)
        self.setHasSearch(hasSearch)
        self.setIsPirate(isPirate)
        self.setCallback(self.openURL)
        
    ## Getters
    
    def getAllAttrs(self):
        
        attrs = super().getAllAttrs()
        attrs["url"] = self.getURL()
        attrs["isMusic"] = self.isMusic()
        attrs["hasSearch"] = self.hasSearch()
        attrs["isPirate"] = self.isPirate()
        
        return attrs
    
    def getURL(self):
        return self.__url
    
    def isMusic(self):
        return self.__isMusic
    
    def hasSearch(self):
        return self.__hasSearch
    
    def isPirate(self):
        return self.__isPirate
    
    ## Setters
    
    def setURL(self, url):
        self.__url = str(url)
        
    def setIsMusic(self, isMusic):
        self.__isMusic = bool(isMusic)
        for menuOption in self.getMenuOptions():
            if menuOption.getText() == TILE.TOGGLE_MUSIC_TEXT and type(menuOption) == ToggleButton:
                menuOption.setValue(self.isMusic())
        
    def setHasSearch(self, hasSearch):
        self.__hasSearch = bool(hasSearch)
        for menuOption in self.getMenuOptions():
            if menuOption.getText() == TILE.TOGGLE_SEARCH_TEXT and type(menuOption) == ToggleButton:
                menuOption.setValue(self.hasSearch())
    
    def setIsPirate(self, isPirate):
        self.__isPirate = bool(isPirate)
        for menuOption in self.getMenuOptions():
            if menuOption.getText() == TILE.TOGGLE_PIRATE_TEXT and type(menuOption) == ToggleButton:
                menuOption.setValue(self.isPirate())
        
    ## Callbacks
    
    def openURL(self):
        incognito = False
        if self.isPirate():
            incognito = True
        webInterface.openURL(self.getURL(), incognito)
    
    def editURL(self):
        return
    
    def toggleIsMusic(self):
        self.setIsMusic(not self.isMusic())
    
    def toggleHasSearch(self):
        self.setHasSearch(not self.hasSearch())
    
    def toggleIsPirate(self):
        self.setIsPirate(not self.isPirate())
"""