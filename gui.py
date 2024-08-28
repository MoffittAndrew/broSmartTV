from global_conf import *
from PyQt5.QtWidgets import *

class Button:
    def __init__(
        this,
        enabled:bool = True,
        width:int = MIN_BUTTON_WIDTH,
        height:int = MIN_BUTTON_HEIGHT,
        text:str = "",
        img = None,
        callback = None,
        navUp = None,
        navRight = None,
        navDown = None,
        navLeft = None,
        navReturn = None,
        menuOptions:list = [],
        isToggle:bool = False,
        toggleVal:bool = True,
    ):
        this.__navButtons = {}
        
        this.setEnabled(enabled)
        this.setWidth(width)
        this.setHeight(height)
        this.setText(text)
        this.setImg(img)
        this.setCallback(callback)
        this.setNavUp(navUp)
        this.setNavRight(navRight)
        this.setNavDown(navDown)
        this.setNavLeft(navLeft)
        this.setNavReturn(navReturn)
        this.setMenuOptions(menuOptions)
        this.setIsToggle(isToggle)
        this.setToggleVal(toggleVal)
        
    ## Getters
    
    def enabled(this):
        return this.__enabled
        
    def getHeight(this):
        return this.__height
    
    def getWidth(this):
        return this.__width
    
    def getText(this):
        return this.__text
            
    def getImg(this):
        return this.__img
    
    def getCallback(this):
        return this.__callback
    
    def getNavButton(this, index: str = "NAV_RIGHT"):
        if index in this.__navButtons.keys():
            return this.__navButtons[index]
        
    def getNavUp(this):
        return this.setNavButton("NAV_UP")
    
    def getNavRight(this):
        return this.setNavButton("NAV_RIGHT")
        
    def getNavDown(this):
        return this.setNavButton("NAV_DOWN")
        
    def getNavLeft(this):
        return this.setNavButton("NAV_LEFT")
    
    def getNavReturn(this):
        return this.setNavButton("RETURN")
    
    def getMenuOption(this, index):
        return this.__menuOptions[index]
    
    def getMenuOptions(this):
        return this.__menuOptions
    
    def isToggle(this):
        return this.__isToggle
    
    def getToggleVal(this):
        return this.__toggleVal
        
    ## Setters
    
    def setEnabled(this, enabled):
        this.__enabled = enabled
        
    def setHeight(this, height):
        if height >= MIN_BUTTON_HEIGHT:
            this.__height = height
            
    def setWidth(this, width):
        if width >= MIN_BUTTON_WIDTH:
            this.__width = width
            
    def setText(this, text):
        this.__text = text
            
    def setImg(this, img):
        this.__img = img
        
    def setCallback(this, callback):
        this.__callback = callback
        
    def setNavButton(this, index, button):
        if index in this.__navButtons.keys():
            this.__navButtons[index] = button
        
    def setNavUp(this, button):
        this.setNavButton("NAV_UP", button)
    
    def setNavRight(this, button):
        this.setNavButton("NAV_RIGHT", button)
        
    def setNavDown(this, button):
        this.setNavButton("NAV_DOWN", button)
        
    def setNavLeft(this, button):
        this.setNavButton("NAV_LEFT", button)
        
    def setNavReturn(this, button):
        this.setNavButton("RETURN", button)
        
    def setMenuOptions(this, menuOptions):
        
        if len(menuOptions) > 0:
            for i in range(len(menuOptions) - 1):
                menuOptions[i + 1].setNavUp(menuOptions[i])
                menuOptions[i].setNavDown(menuOptions[i + 1])
                menuOptions[i].setNavReturn(this)
            menuOptions[-1].setNavReturn(this)
            
        this.__menuOptions = menuOptions
        
    def setIsToggle(this, isToggle):
        this.__isToggle = isToggle
        
    def setToggleVal(this, toggleVal = None):
        this.__toggleVal = toggleVal
    
    # Other
    
    def enable(this):
        this.setEnabled(True)
        
    def disable(this):
        this.setEnabled(False)
    
    def addMenuOption(this, menuOption = None):
        if menuOption != None:
            if len(this.getMenuOptions()) > 0:
                lastMenuOption = this.getMenuOptions()[-1]
                menuOption.setNavUp(lastMenuOption)
                lastMenuOption.setNavDown(menuOption)
            menuOption.setNavReturn(this)
            this.__menuOptions.append(menuOption)
            
    def activate(this):
        if this.enabled():
            callback = this.getCallback()
            callback()
            
    def toggle(this):
        if this.isToggle():
            this.setToggleVal(not this.getToggleVal())

class Tile(Button):
    def __init__(
        this,
        name:str = "new tile",
        url:str = "",
        hasSearch:bool = False,
        width:int = TILE_WIDTH,
        height:int = TILE_HEIGHT,
        *args,
        **kwargs,
    ):
        menuOptions = [
            Button(text = TILE_EDIT_NAME_TEXT, callback = this.editName),
            Button(text = TILE_EDIT_URL_TEXT, callback = this.editURL),
            Button(text = TILE_EDIT_IMG_TEXT, callback = this.editImg),
            Button(text = TILE_TOGGLE_SEARCH_TEXT, callback = this.toggleHasSearch, isToggle = True),
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
            if menuOption.getText() == TILE_TOGGLE_SEARCH_TEXT and menuOption.isToggle():
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