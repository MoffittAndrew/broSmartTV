print("Importing input interface...")

from globals import INPUT
from button import Button

from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QPoint

class InputInterface(QLabel):
    def __init__(this, selectedButton = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.setWebMode(False)
        this.setWidth(0)
        this.setHeight(0)
        this.setPos(QPoint(0, 0))
        this.setSelectedButton(selectedButton)
        #this.show()
        
        this.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        this.setAttribute(Qt.WA_TranslucentBackground)
    
    def inWebMode(this):
        return this.__webMode

    def getWebDriver(this):
        return this.__webdriver
    
    def getWidth(this):
        return this.__width

    def getHeight(this):
        return this.__height
    
    def getPos(this):
        return this.__pos
    
    def getSelectedButton(this):
        return this.__selectedButton
    
    def setWebMode(this, webMode = True, webdriver = None):
        this.__webMode = webMode
        if not this.inWebMode() or webdriver is not None:
            this.setWebDriver(webdriver)
    
    def setWebDriver(this, webdriver):
        this.__webdriver = webdriver
    
    def setWidth(this, width):
        this.__width = width
        this.setFixedWidth(width)

    def setHeight(this, height):
        this.__height = height
        this.setFixedHeight(height)
    
    def setPos(this, pos):
        this.__pos = pos
        this.move(pos)
    
    def setSelectedButton(this, button):
        this.__selectedButton = button
        if button is not None:
            if isinstance(button, Button):
                width = button.getWidth()
                height = button.getHeight()
                pos = button.getPos()
            else:
                rect = button.rect
                width = rect["width"]
                height = rect["height"]
                pos = QPoint(int(rect["x"]), int(rect["y"]))
            
            this.setWidth(width)
            this.setHeight(height)
            this.setPos(pos)
            print(this.getPos(), this.getWidth(), this.getHeight())
    
    def receive(this, data):
        if data == INPUT.SELECT:
            this.select()
        elif isinstance(data, str) and data.startswith(INPUT.NAV_PREFIX):
            this.navigate(data)
        elif data == INPUT.RETURN:
            this.back()
    
    def select(this):
        selectedButton = this.getSelectedButton()
        if selectedButton is not None:
            selectedButton.click()
            if this.inWebMode() and not isinstance(selectedButton, Button):
                driver = this.getWebDriver()
                if not driver.elementExists(selectedButton):
                    this.setSelectedButton(driver.getDefaultElement())
        else:
            print("No initial selected button set.")
    
    def navigate(this, index:str = INPUT.NAV_RIGHT):
        selectedButton = this.getSelectedButton()
        if selectedButton is not None:
            if not this.inWebMode():
                newButton = selectedButton.getNavButton(index)
            
            else:
                driver = this.getWebDriver()
                if driver is not None:
                    if index == INPUT.NAV_UP:
                        newButtonLocator = driver.getElementAbove(selectedButton)
                    elif index == INPUT.NAV_RIGHT:
                        newButtonLocator = driver.getElementRight(selectedButton)
                    elif index == INPUT.NAV_DOWN:
                        newButtonLocator = driver.getElementBelow(selectedButton)
                    elif index == INPUT.NAV_LEFT:
                        newButtonLocator = driver.getElementLeft(selectedButton)
                    newButton = driver.find_element(newButtonLocator)
                else:
                    print("No webdriver set!")
            
            if newButton is not None:
                this.setSelectedButton(newButton)
        else:
            print("No initial selected button set.")
    
    def navUp(this):
        this.navigate(INPUT.NAV_UP)
    
    def navRight(this):
        this.navigate(INPUT.NAV_RIGHT)
    
    def navDown(this):
        this.navigate(INPUT.NAV_DOWN)
    
    def navLeft(this):
        this.navigate(INPUT.NAV_LEFT)
    
    def back(this):
        if this.inWebMode():
            this.getWebDriver().quit()
    
    def paintEvent(this, event=None):
        painter = QtGui.QPainter()
        painter.begin(this)
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        painter.setPen(QtGui.QPen(Qt.red, 5, Qt.SolidLine))
        painter.drawRect(0, 0, this.getWidth(), this.getHeight())
        
        painter.restore()
        painter.end()

inputInterface = InputInterface()