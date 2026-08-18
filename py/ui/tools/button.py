print("Importing button class...")

import inspect

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
        textSize:int = GUI.BUTTON.TEXT_SIZE,
        roundness:int = GUI.BUTTON.ROUNDNESS,
        borderThickness:int = GUI.BUTTON.BORDER_THICKNESS,
        color:QtGui.QColor = GUI.BUTTON.COLOR,
        backgroundColor:QtGui.QColor = GUI.BUTTON.BG_COLOR,
        text:str = "",
        img = None,
        clickCallback = None,
        menuCallback = None,
        returnCallback = None,
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
        self.setTextSize(textSize)
        self.setRoundness(roundness)
        self.setBorderThickness(borderThickness)
        self.setColor(color)
        self.setBgColor(backgroundColor)
        self.setImg(img)
        self.setText(text)
        self.setClickCallback(clickCallback)
        self.setMenuCallback(menuCallback)
        self.setReturnCallback(returnCallback)
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

    def getTextSize(self):
        return self.__textSize

    def getRoundness(self):
        return self.__roundness
    
    def getBorderThickness(self):
        return self.__borderThickness
    
    def getColor(self):
        return self.__color
    
    def getBgColor(self):
        return self.__bgColor
    
    def getText(self):
        return self.__text
    
    def getImg(self):
        return self.__img
    
    def getClickCallback(self):
        return self.__clickCallback, self.__clickCallbackArgs, self.__clickCallbackKwargs
    
    def getMenuCallback(self):
        return self.__menuCallback, self.__menuCallbackArgs, self.__menuCallbackKwargs
    
    def getReturnCallback(self):
        return self.__returnCallback, self.__returnCallbackArgs, self.__returnCallbackKwargs
    
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
    
    def setEnabled(self, a0: bool):
        enabled = bool(a0)
        self.__enabled = enabled
        # Keep QLabel visually enabled to avoid Qt auto-tinting the full pixmap.
        super().setEnabled(True)
        self.__needsDraw = True
        if self.pixmap() is not None:
            self.draw()
    
    def resize(self, w, h=None):
        if h is None:
            super().resize(w)
            self.__needsDraw = True
            return

        if w >= GUI.BUTTON.MIN_WIDTH:
            w = int(w)
        if h >= GUI.BUTTON.MIN_HEIGHT:
            h = int(h)

        super().resize(w, h)
        self.__needsDraw = True
    
    def setTextSize(self, textSize: int):
        self.__textSize = textSize
    
    def setRoundness(self, roundness: int):
        self.__roundness = roundness
    
    def setBorderThickness(self, borderThickness: int):
        self.__borderThickness = borderThickness
    
    def setColor(self, color: QtGui.QColor):
        self.__color = color
        self.__needsDraw = True
    
    def setBgColor(self, color: QtGui.QColor):
        self.__bgColor = color
        self.__needsDraw = True
    
    def setText(self, a0):
        self.__text = str(a0)
        if self.getImg() is None:
            self.__needsDraw = True
    
    def setImg(self, img):
        self.__img = img
        self.__needsDraw = True
    
    def setClickCallback(self, callback, *args, **kwargs):
        self.__clickCallback = callback
        self.__clickCallbackArgs = args
        self.__clickCallbackKwargs = kwargs

    def setMenuCallback(self, callback, *args, **kwargs):
        self.__menuCallback = callback
        self.__menuCallbackArgs = args
        self.__menuCallbackKwargs = kwargs
    
    def setReturnCallback(self, callback, *args, **kwargs):
        self.__returnCallback = callback
        self.__returnCallbackArgs = args
        self.__returnCallbackKwargs = kwargs
    
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
            callback, args, kwargs = self.getClickCallback()
            if callback is not None:
                await callback(*args, **kwargs)
            else:
                print(f"Button '{self.getText()}' has no click callback!")
    
    async def menu(self):
        if self.enabled():
            callback, args, kwargs = self.getMenuCallback()
            if callback is not None:
                await callback(*args, **kwargs)
            else:
                print(f"Button '{self.getText()}' has no menu callback!")
    
    async def back(self):
        if self.enabled():
            callback, args, kwargs = self.getReturnCallback()
            if callback is not None:
                await callback(*args, **kwargs)
            else:
                print(f"Button '{self.getText()}' has no return callback!")
    
    def draw(self):
        if self.__needsDraw:
            canvas = self.pixmap()
            if canvas is None:
                return

            canvas.fill(Qt.transparent)
            painter = QtGui.QPainter(canvas)
            painter.save()
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

            if self.getImg() is None:
                borderAndTextColor = self.getColor() if self.enabled() else GUI.BUTTON.COLOR_DISABLED
                painter.setBrush(QtGui.QBrush(self.getBgColor()))
                painter.setPen(QtGui.QPen(borderAndTextColor, self.getBorderThickness(), Qt.SolidLine))
                painter.drawRoundedRect(
                    int(self.getBorderThickness()/2),
                    int(self.getBorderThickness()/2),
                    self.width() - self.getBorderThickness(),
                    self.height() - self.getBorderThickness(),
                    self.getRoundness(),
                    self.getRoundness(),
                )

                if self.getText() != "":
                    font = QtGui.QFont()
                    font.setFamily('Times')
                    font.setPointSize(self.getTextSize())
                    painter.setFont(font)
                    painter.setPen(QtGui.QPen(borderAndTextColor))

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
        fetchValueCallback=None,
        trueText = "",
        falseText = "",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.setFetchValueCallback(fetchValueCallback)
        self.setTrueText(trueText)
        self.setFalseText(falseText)
        self.refresh()
        
    ## Getters
    
    def getValue(self):
        fetchValueCallback, args, kwargs = self.getFetchValueCallback()
        if fetchValueCallback is None:
            raise RuntimeError("ToggleButton requires a fetchValueCallback")
        return bool(fetchValueCallback(*args, **kwargs))
    
    def getFetchValueCallback(self):
        return self.__fetchValueCallback, self.__fetchValueCallbackArgs, self.__fetchValueCallbackKwargs
    
    def getTrueText(self):
        return self.__trueText
    
    def getFalseText(self):
        return self.__falseText
        
    ## Setters
        
    def setFetchValueCallback(self, callback, *args, **kwargs):
        self.__fetchValueCallback = callback
        self.__fetchValueCallbackArgs = args
        self.__fetchValueCallbackKwargs = kwargs
    
    def setTrueText(self, trueText = ""):
        self.__trueText = str(trueText)
    
    def setFalseText(self, falseText = ""):
        self.__falseText = str(falseText)
    
    # Other

    def _updateText(self):
        self.setText(self.getTrueText() if self.getValue() else self.getFalseText())

    def draw(self):
        self._updateText()
        super().draw()
