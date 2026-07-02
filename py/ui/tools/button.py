print("Importing button class...")

from globals import INPUT, GUI
from ui.gui import CustomQLabel

from PyQt5 import QtGui
from PyQt5.QtCore import Qt

class Button(CustomQLabel):
    def __init__(
        self,
        enabled:bool = True,
        width:int = GUI.BUTTON.MIN_WIDTH,
        height:int = GUI.BUTTON.MIN_HEIGHT,
        roundness:int = GUI.BUTTON.ROUNDNESS,
        borderThickness:int = GUI.BUTTON.BORDER_THICKNESS,
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
        
        self.__navButtons = {}
        
        self.setEnabled(enabled)
        self.resize(width, height)
        self.setRoundness(roundness)
        self.setBorderThickness(borderThickness)
        self.setImg(img)
        self.setText(text)
        self.setCallback(callback)
        self.setNavUp(navUp)
        self.setNavRight(navRight)
        self.setNavDown(navDown)
        self.setNavLeft(navLeft)
        self.setMenuOptions(menuOptions)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.__needsDraw = True
        canvas = QtGui.QPixmap(self.width(), self.height())
        self.setPixmap(canvas)
        self.draw()
    
    ## Getters
    
    def enabled(self):
        return self.__enabled

    def getRoundness(self):
        return self.__roundness
    
    def getBorderThickness(self):
        return self.__borderThickness
    
    def getText(self):
        return self.__text
    
    def getImg(self):
        return self.__img
    
    def getCallback(self):
        return self.__callback, self.__callbackArgs, self.__callbackKwargs
    
    def getNavButton(self, index: str = INPUT.NAV_RIGHT):
        if index in self.__navButtons.keys():
            return self.__navButtons[index]
    
    def getNavUp(self):
        return self.getNavButton(INPUT.NAV_UP)
    
    def getNavRight(self):
        return self.getNavButton(INPUT.NAV_RIGHT)
    
    def getNavDown(self):
        return self.getNavButton(INPUT.NAV_DOWN)
    
    def getNavLeft(self):
        return self.getNavButton(INPUT.NAV_LEFT)

    def getMenuOption(self, index):
        return self.__menuOptions[index]
    
    def getMenuOptions(self):
        return self.__menuOptions
    
    ## Setters
    
    def setEnabled(self, enabled):
        self.__enabled = bool(enabled)
    
    def resize(self, w, h):
        if w >= GUI.BUTTON.MIN_WIDTH:
            w = int(w)
        if h >= GUI.BUTTON.MIN_HEIGHT:
            h = int(h)
        
        super().resize(w, h)
    
    def setRoundness(self, roundness):
        self.__roundness = roundness
    
    def setBorderThickness(self, borderThickness):
        self.__borderThickness = borderThickness
    
    def setText(self, text):
        self.__text = str(text)
        if self.getImg() is None:
            self.__needsDraw = True
    
    def setImg(self, img):
        self.__img = img
        if self.getImg() is None:
            self.__needsDraw = True
    
    def setCallback(self, callback, *args, **kwargs):
        self.__callback = callback
        self.__callbackArgs = args
        self.__callbackKwargs = kwargs
    
    def setNavButton(self, index, button):
        self.__navButtons[index] = button
    
    def setNavUp(self, button):
        self.setNavButton("NAV_UP", button)
    
    def setNavRight(self, button):
        self.setNavButton("NAV_RIGHT", button)
    
    def setNavDown(self, button):
        self.setNavButton("NAV_DOWN", button)
    
    def setNavLeft(self, button):
        self.setNavButton("NAV_LEFT", button)
    
    def setMenuOptions(self, menuOptions):
        
        if len(menuOptions) > 0:
            for i in range(len(menuOptions) - 1):
                menuOptions[i + 1].setNavUp(menuOptions[i])
                menuOptions[i].setNavDown(menuOptions[i + 1])
        
        self.__menuOptions = menuOptions
    
    # Other
    
    def enable(self):
        self.setEnabled(True)
    
    def disable(self):
        self.setEnabled(False)
    
    def addMenuOption(self, menuOption = None):
        if menuOption is not None:
            if len(self.getMenuOptions()) > 0:
                lastMenuOption = self.getMenuOptions()[-1]
                menuOption.setNavUp(lastMenuOption)
                lastMenuOption.setNavDown(menuOption)
            self.__menuOptions.append(menuOption)
    
    async def click(self):
        if self.enabled():
            callback, args, kwargs = self.getCallback()
            if callback is not None:
                await callback(*args, **kwargs)
            else:
                print(f"Button {self.getText()} has no callback!")
    
    def draw(self):
        if self.__needsDraw:
            painter = QtGui.QPainter(self.pixmap())
            painter.save()
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

            if self.getImg() is None and self.getText() != "":
                painter.setPen(QtGui.QPen(GUI.BUTTON.BORDER_COLOR, self.getBorderThickness(), Qt.SolidLine))
                painter.drawRoundedRect(
                    int(self.getBorderThickness()/2),
                    int(self.getBorderThickness()/2),
                    self.width() - self.getBorderThickness(),
                    self.height() - self.getBorderThickness(),
                    self.getRoundness(),
                    self.getRoundness(),
                )

                font = QtGui.QFont()
                font.setFamily('Times')
                font.setPointSize(40)
                painter.setFont(font)

                painter.drawText(0, 0, self.width(), self.height(), Qt.AlignCenter, self.getText())
            
            painter.restore()
            painter.end()
        self.__needsDraw = False
    
    def __str__(self):
        return self.getText()
    
    def equals(self, button):
        if self.getText() == button.getText():
            return True
        return False



class ToggleButton(Button):
    def __init__(
        self,
        value:bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        self.setValue(value)
        
    ## Getters
    
    def getValue(self):
        return self.__value
        
    ## Setters
        
    def setValue(self, value = None):
        self.__value = bool(value)
    
    # Other
    
    def toggle(self):
        self.setValue(not self.getValue())



class NavBarButton(Button):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(width=GUI.NAVBAR.BUTTON_WIDTH, height=GUI.NAVBAR.BUTTON_HEIGHT, *args, **kwargs)