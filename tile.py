from globals import TILE
from button import Button, ToggleButton

class Tile(Button):
    def __init__(
        this,
        index:int = None,
        name:str = "new tile",
        filepath:str = "",
        *args,
        **kwargs,
    ):
        super().__init__(width = TILE.WIDTH, height = TILE.HEIGHT, *args, **kwargs)
        
        menuOptions = [
            Button(text = TILE.EDIT_NAME_TEXT, callback = this.editName),
            Button(text = TILE.EDIT_IMG_TEXT, callback = this.editImg),
        ]
        for menuOption in menuOptions:
            this.addMenuOption(menuOption)
        
        this.setIndex(index)
        this.setName(name)
        this.setFilepath(filepath)
        
    ## Getters
    
    def getIndex(this):
        return this.__index
    
    def getName(this):
        return this.__name
    
    def getFilepath(this):
        return this.__filepath
    
    ## Setters
    
    def setIndex(this, index):
        this.__index = int(index)
    
    def setName(this, name):
        this.__name = str(name)
        this.setText(this.getName())
        
    def setFilepath(this, filepath):
        this.__filepath = str(filepath)
        
    ## Callbacks
    
    def editName(this):
        return
    
    def editImg(this):
        return


class DeviceTile(Tile):
    def __init__(
        this,
        inputChannel:str = "",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        menuOptions = [
            Button(text = TILE.EDIT_INPUT_TEXT, callback = this.editInputChannel),
        ]
        for menuOption in menuOptions:
            this.addMenuOption(menuOption)
        
        this.setInputChannel(inputChannel)
        
    ## Getters
    
    def getInputChannel(this):
        return this.__inputChannel
    
    ## Setters
    
    def setInputChannel(this, inputChannel):
        this.__inputChannel = str(inputChannel)
        
    ## Callbacks
    
    def editInputChannel(this):
        return


class WebTile(Tile):
    def __init__(
        this,
        url:str = "",
        isMusic:bool = False,
        hasSearch:bool = True,
        isPirate:bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        menuOptions = [
            Button(text = TILE.EDIT_URL_TEXT, callback = this.editURL),
            ToggleButton(text = TILE.TOGGLE_MUSIC_TEXT, callback = this.toggleIsMusic),
            ToggleButton(text = TILE.TOGGLE_SEARCH_TEXT, callback = this.toggleHasSearch),
            ToggleButton(text = TILE.TOGGLE_PIRATE_TEXT, callback = this.toggleIsPirate),
        ]
        for menuOption in menuOptions:
            this.addMenuOption(menuOption)
        
        this.setURL(url)
        this.setIsMusic(isMusic)
        this.setHasSearch(hasSearch)
        this.setIsPirate(isPirate)
        
    ## Getters
    
    def getURL(this):
        return this.__url
    
    def isMusic(this):
        return this.__isMusic
    
    def hasSearch(this):
        return this.__hasSearch
    
    def isPirate(this):
        return this.__isPirate
    
    ## Setters
    
    def setURL(this, url):
        this.__url = str(url)
        
    def setIsMusic(this, isMusic):
        this.__isMusic = bool(isMusic)
        for menuOption in this.getMenuOptions():
            if menuOption.getText() == TILE.TOGGLE_MUSIC_TEXT and type(menuOption) == ToggleButton:
                menuOption.setValue(this.isMusic())
        
    def setHasSearch(this, hasSearch):
        this.__hasSearch = bool(hasSearch)
        for menuOption in this.getMenuOptions():
            if menuOption.getText() == TILE.TOGGLE_SEARCH_TEXT and type(menuOption) == ToggleButton:
                menuOption.setValue(this.hasSearch())
    
    def setIsPirate(this, isPirate):
        this.__isPirate = bool(isPirate)
        for menuOption in this.getMenuOptions():
            if menuOption.getText() == TILE.TOGGLE_PIRATE_TEXT and type(menuOption) == ToggleButton:
                menuOption.setValue(this.isPirate())
        
    ## Callbacks
    
    def editURL(this):
        return
    
    def toggleIsMusic(this):
        this.setIsMusic(not this.isMusic())
    
    def toggleHasSearch(this):
        this.setHasSearch(not this.hasSearch())
    
    def toggleIsPirate(this):
        this.setIsPirate(not this.isPirate())