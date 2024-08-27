from global_conf import MIN_BUTTON_HEIGHT, MIN_BUTTON_WIDTH
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

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
        this.__enabled
        this.__width
        this.__height
        this.__text
        this.__img
        this.__callback
        this.__adjButtons = {}
        this.__menuOptions = []
        
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
        
    def getHeight(this):
        return this.__height
    
    def getWidth(this):
        return this.__width
    
    def getAdjButton(this, index: str = "right"):
        if index in this.__adjButtons.keys:
            return this.__adjButtons[index]
        
    def getAdjUp(this):
        return this.setAdjButton("up")
    
    def getAdjRight(this):
        return this.setAdjButton("right")
        
    def getAdjDown(this):
        return this.setAdjButton("down")
        
    def getAdjLeft(this):
        return this.setAdjButton("left")
    
    def getMenuOption(this, index: int = 0):
        return this.__menuOptions[index]
    
    def getMenuOptions(this):
        return this.__menuOptions
        
    ## Setters
    
    def setEnabled(this, enabled: bool = True):
        this.__enabled = enabled
        
    def setHeight(this, height: int):
        if height >= MIN_BUTTON_HEIGHT:
            this.__height = height
            
    def setWidth(this, width: int):
        if width >= MIN_BUTTON_WIDTH:
            this.__width = width
            
    def setText(this, text: str = None):
        this.__text = text
            
    def setImg(this, img = None):
        this.__img = img
        
    def setCallback(this, callback = None):
        this.__callback = callback
        
    def setAdjButton(this, index: str = "right", button = None):
        if index in this.__adjButtons.keys:
            this.__adjButtons[index] = button
        
    def setAdjUp(this, button = None):
        this.setAdjButton("up", button)
    
    def setAdjRight(this, button = None):
        this.setAdjButton("right", button)
        
    def setAdjDown(this, button = None):
        this.setAdjButton("down", button)
        
    def setAdjLeft(this, button = None):
        this.setAdjButton("left", button)
        
    def setMenuOptions(this, menuOptions: list = []):
        this.__menuOptions = menuOptions
    
    # Other
    
    def enable(this):
        this.setEnabled(True)
        
    def disable(this):
        this.setEnabled(False)
    
    def addMenuOption(this, menuOption = None):
        if menuOption != None:
            this.__menuOptions.append(menuOption)
            
            
defaultButton = Button()