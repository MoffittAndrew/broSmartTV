from global_conf import MIN_BUTTON_HEIGHT, MIN_BUTTON_WIDTH, DEFAULT_TILE_WIDTH, DEFAULT_TILE_HEIGHT
from PyQt5.QtWidgets import *

class Button:
    def __init__(
        this,
        enabled: bool = True,
        width: int = MIN_BUTTON_WIDTH,
        height: int = MIN_BUTTON_HEIGHT,
        text: str = "",
        img = None,
        callback = None,
        adjUp = None,
        adjRight = None,
        adjDown = None,
        adjLeft = None,
        menuOptions: list = [],
    ):
        this.__adjButtons = {}
        
        this.setEnabled(enabled)
        this.setWidth(width)
        this.setHeight(height)
        this.setText(text)
        this.setImg(img)
        this.setCallback(callback)
        this.setAdjUp(adjUp)
        this.setAdjRight(adjRight)
        this.setAdjDown(adjDown)
        this.setAdjLeft(adjLeft)
        this.setMenuOptions(menuOptions)
        
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
    
    def getAdjButton(this, index: str = "NAV_RIGHT"):
        if index in this.__adjButtons.keys():
            return this.__adjButtons[index]
        
    def getAdjUp(this):
        return this.setAdjButton("NAV_UP")
    
    def getAdjRight(this):
        return this.setAdjButton("NAV_RIGHT")
        
    def getAdjDown(this):
        return this.setAdjButton("NAV_DOWN")
        
    def getAdjLeft(this):
        return this.setAdjButton("NAV_LEFT")
    
    def getMenuOption(this, index):
        return this.__menuOptions[index]
    
    def getMenuOptions(this):
        return this.__menuOptions
        
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
        
    def setAdjButton(this, index, button):
        if index in this.__adjButtons.keys():
            this.__adjButtons[index] = button
        
    def setAdjUp(this, button):
        this.setAdjButton("NAV_UP", button)
    
    def setAdjRight(this, button):
        this.setAdjButton("NAV_RIGHT", button)
        
    def setAdjDown(this, button):
        this.setAdjButton("NAV_DOWN", button)
        
    def setAdjLeft(this, button):
        this.setAdjButton("NAV_LEFT", button)
        
    def setMenuOptions(this, menuOptions):
        this.__menuOptions = menuOptions
    
    # Other
    
    def enable(this):
        this.setEnabled(True)
        
    def disable(this):
        this.setEnabled(False)
    
    def addMenuOption(this, menuOption = None):
        if menuOption != None:
            this.__menuOptions.append(menuOption)
            
    def activate(this):
        if this.enabled():
            callback = this.getCallback()
            callback()

class Tile(Button):
    def __init__(
        this,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)