from globals import BUTTON

class Button:
    def __init__(
        this,
        enabled:bool = True,
        width:int = BUTTON.MIN_WIDTH,
        height:int = BUTTON.MIN_HEIGHT,
        text:str = "",
        img = None,
        callback = None,
        navUp = None,
        navRight = None,
        navDown = None,
        navLeft = None,
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
        if height >= BUTTON.MIN_HEIGHT:
            this.__height = height
            
    def setWidth(this, width):
        if width >= BUTTON.MIN_WIDTH:
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
        
    def setMenuOptions(this, menuOptions):
        
        if len(menuOptions) > 0:
            for i in range(len(menuOptions) - 1):
                menuOptions[i + 1].setNavUp(menuOptions[i])
                menuOptions[i].setNavDown(menuOptions[i + 1])
            
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
        this.setToggleVal(not this.getToggleVal())
        


class ToggleButton(Button):
    def __init__(
        this,
        value:bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        this.setValue(value)
        
    ## Getters
    
    def getValue(this):
        return this.__value
        
    ## Setters
        
    def setValue(this, value = None):
        this.__value = value
    
    # Other
            
    def toggle(this):
        this.setValue(not this.getValue())