print("Importing button class...")

from globals import BUTTON, INPUT

from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QPoint

class Button(QLabel):
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
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        this.__navButtons = {}
        
        this.setEnabled(enabled)
        this.setWidth(width)
        this.setHeight(height)
        this.setImg(img)
        this.setText(text)
        this.setCallback(callback)
        this.setNavUp(navUp)
        this.setNavRight(navRight)
        this.setNavDown(navDown)
        this.setNavLeft(navLeft)
        this.setMenuOptions(menuOptions)
        this.setParentPos(QPoint(0, 0))
        
        this.__needsDraw = True
        canvas = QtGui.QPixmap(this.getWidth(), this.getHeight())
        this.setPixmap(canvas)
        this.draw()
    
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
        return this.__callback, this.__callbackArgs, this.__callbackKwargs
    
    def getNavButton(this, index: str = INPUT.NAV_RIGHT):
        if index in this.__navButtons.keys():
            return this.__navButtons[index]
    
    def getNavUp(this):
        return this.getNavButton(INPUT.NAV_UP)
    
    def getNavRight(this):
        return this.getNavButton(INPUT.NAV_RIGHT)
    
    def getNavDown(this):
        return this.getNavButton(INPUT.NAV_DOWN)
    
    def getNavLeft(this):
        return this.getNavButton(INPUT.NAV_LEFT)

    def getMenuOption(this, index):
        return this.__menuOptions[index]
    
    def getMenuOptions(this):
        return this.__menuOptions
    
    def getParentPos(this):
        return this.__parentPos
    
    def getPos(this):
        return this.getParentPos() + this.pos()
    
    ## Setters
    
    def setEnabled(this, enabled):
        this.__enabled = bool(enabled)
    
    def setHeight(this, height):
        if height >= BUTTON.MIN_HEIGHT:
            this.__height = int(height)
    
    def setWidth(this, width):
        if width >= BUTTON.MIN_WIDTH:
            this.__width = int(width)
    
    def setText(this, text):
        this.__text = str(text)
        if this.getImg() is None:
            this.__needsDraw = True
    
    def setImg(this, img):
        this.__img = img
        if this.getImg() is None:
            this.__needsDraw = True
    
    def setCallback(this, callback, *args, **kwargs):
        this.__callback = callback
        this.__callbackArgs = args
        this.__callbackKwargs = kwargs
    
    def setNavButton(this, index, button):
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
    
    def setParentPos(this, pos):
        this.__parentPos = pos
    
    # Other
    
    def enable(this):
        this.setEnabled(True)
    
    def disable(this):
        this.setEnabled(False)
    
    def addMenuOption(this, menuOption = None):
        if menuOption is not None:
            if len(this.getMenuOptions()) > 0:
                lastMenuOption = this.getMenuOptions()[-1]
                menuOption.setNavUp(lastMenuOption)
                lastMenuOption.setNavDown(menuOption)
            this.__menuOptions.append(menuOption)
    
    def click(this):
        if this.enabled():
            callback, args, kwargs = this.getCallback()
            if callback is not None:
                callback(*args, **kwargs)
            else:
                print(f"Button {this.getText()} has no callback!")
    
    def draw(this):
        if this.__needsDraw:
            painter = QtGui.QPainter(this.pixmap())

            if this.getImg() is None and this.getText() != "":
                pen = QtGui.QPen()
                pen.setWidth(1)
                pen.setColor(QtGui.QColor('white'))
                painter.setPen(pen)
                
                painter.setBrush(QtGui.QBrush(Qt.black, Qt.SolidPattern))
                painter.drawRect(0, 0, this.getWidth(), this.getHeight())

                font = QtGui.QFont()
                font.setFamily('Times')
                font.setPointSize(40)
                painter.setFont(font)

                painter.drawText(0, 0, this.getWidth(), this.getHeight(), Qt.AlignCenter, this.getText())
            
            painter.end()
        this.__needsDraw = False
    
    def __str__(this):
        return this.getText()
    
    def equals(this, button):
        if this.getText() == button.getText():
            return True
        return False



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
        this.__value = bool(value)
    
    # Other
            
    def toggle(this):
        this.setValue(not this.getValue())