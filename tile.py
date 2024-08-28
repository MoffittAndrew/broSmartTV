from globals import TILE
from button import Button

class Tile(Button):
    def __init__(
        this,
        name:str = "new tile",
        url:str = "",
        hasSearch:bool = False,
        width:int = TILE.WIDTH,
        height:int = TILE.HEIGHT,
        *args,
        **kwargs,
    ):
        menuOptions = [
            Button(text = TILE.EDIT_NAME_TEXT, callback = this.editName),
            Button(text = TILE.EDIT_URL_TEXT, callback = this.editURL),
            Button(text = TILE.EDIT_IMG_TEXT, callback = this.editImg),
            Button(text = TILE.TOGGLE_SEARCH_TEXT, callback = this.toggleHasSearch, isToggle = True),
        ],
        super().__init__(
            width = width,
            height = height,
            menuOptions = menuOptions,
            *args,
            **kwargs
        )
        
        this.setName(name)
        this.setURL(url)
        this.setHasSearch(hasSearch)
        
    ## Getters
    
    def getName(this):
        return this.__name
    
    def getURL(this):
        return this.__url
    
    def hasSearch(this):
        return this.__hasSearch
    
    ## Setters
    
    def setName(this, name):
        this.__name = name
        this.setText(name)
    
    def setURL(this, url):
        this.__url = url
        
    def setHasSearch(this, hasSearch):
        this.__hasSearch = hasSearch
        for menuOption in this.getMenuOptions():
            if menuOption.getText() == TILE.TOGGLE_SEARCH_TEXT and menuOption.isToggle():
                menuOption.setToggleVal(hasSearch)
        
    ## Other
    
    def editName(this):
        return
    
    def editURL(this):
        return
    
    def editImg(this):
        return
    
    def toggleHasSearch(this):
        this.setHasSearch(not this.hasSearch())