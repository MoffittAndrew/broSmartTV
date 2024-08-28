from globals import TILE
from button import Button

class Tile(Button):
    def __init__(
        this,
        name:str = "new tile",
        width:int = TILE.WIDTH,
        height:int = TILE.HEIGHT,
        *args,
        **kwargs,
    ):
        menuOptions = [
            Button(text = TILE.EDIT_NAME_TEXT, callback = this.editName),
            Button(text = TILE.EDIT_IMG_TEXT, callback = this.editImg),
        ]
        super().__init__(
            width = width,
            height = height,
            menuOptions = menuOptions,
            *args,
            **kwargs
        )
        
        this.setName(name)
        
    ## Getters
    
    def getName(this):
        return this.__name
    
    ## Setters
    
    def setName(this, name):
        this.__name = name
        this.setText(name)
        
    ## Callbacks
    
    def editName(this):
        return
    
    def editImg(this):
        return


class WebTile(Tile):
    def __init__(
        this,
        url:str = "",
        hasSearch:bool = False,
        *args,
        **kwargs,
    ):
        addMenuOptions = [
            Button(text = TILE.EDIT_URL_TEXT, callback = this.editURL),
            Button(text = TILE.TOGGLE_SEARCH_TEXT, callback = this.toggleHasSearch, isToggle = True),
        ]
        super().__init__(
            *args,
            **kwargs
        )
        
        this.setURL(url)
        this.setHasSearch(hasSearch)
        
        for menuOption in addMenuOptions:
            this.addMenuOption(menuOption)
        
    ## Getters
    
    def getURL(this):
        return this.__url
    
    def hasSearch(this):
        return this.__hasSearch
    
    ## Setters
    
    def setURL(this, url):
        this.__url = url
        
    def setHasSearch(this, hasSearch):
        this.__hasSearch = hasSearch
        for menuOption in this.getMenuOptions():
            if menuOption.getText() == TILE.TOGGLE_SEARCH_TEXT and menuOption.isToggle():
                menuOption.setToggleVal(hasSearch)
        
    ## Callbacks
    
    def editURL(this):
        return
    
    def toggleHasSearch(this):
        this.setHasSearch(not this.hasSearch())


class DeviceTile(Tile):
    def __init__(
        this,
        inputChannel:str = "",
        *args,
        **kwargs,
    ):
        addMenuOptions = [
            Button(text = TILE.EDIT_URL_TEXT, callback = this.editInputChannel),
        ]
        super().__init__(
            *args,
            **kwargs
        )
        
        this.setInputChannel(inputChannel)
        
        for menuOption in addMenuOptions:
            this.addMenuOption(menuOption)
        
    ## Getters
    
    def getInputChannel(this):
        return this.__inputChannel
    
    ## Setters
    
    def setURL(this, inputChannel):
        this.__inputChannel = inputChannel
        
    ## Callbacks
    
    def editInputChannel(this):
        return