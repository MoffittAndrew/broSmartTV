print("Importing input interface...")

from globals import INPUT, GUI, PROJECTOR
from button import Button

from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QPoint, QCoreApplication

import asyncio

class InputInterface(QLabel):
    def __init__(this, selectedButton = None, projectorInterface = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.setMode(INPUT.MODES.GUI)
        this.setWidth(0)
        this.setHeight(0)
        this.setPos(QPoint(0, 0))
        this.setSelectedButton(selectedButton)
        this.setProjectorInterface(projectorInterface)
        this.__backlog = []
        this.__isProcessingBacklog = False
        
        this.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        this.setAttribute(Qt.WA_TranslucentBackground)
    
    def inGUIMode(this):
        return this.getMode() == INPUT.MODES.GUI
    
    def inProjectorMode(this):
        return this.getMode() == INPUT.MODES.PROJECTOR

    def inWebMode(this):
        return this.getMode() == INPUT.MODES.WEB

    def inOtherMode(this):
        return this.getMode() == INPUT.MODES.OTHER
    
    def getMode(this):
        return this.__mode

    def getWebDriver(this):
        return this.__webdriver
    
    def getWidth(this):
        return this.width()

    def getHeight(this):
        return this.height()
    
    def getPos(this):
        return this.__pos
    
    def getSelectedButton(this):
        return this.__selectedButton

    def getProjectorInterface(this):
        return this.__projectorInterface
    
    def setMode(this, mode = INPUT.MODES.GUI):
        if mode == INPUT.MODES.PROJECTOR and this.getProjectorInterface() is None:
            print("Cannot set input interface to projector mode, no projector interface has been set!")
        else:
            this.__mode = mode
    
    def setWebDriver(this, webdriver):
        this.__webdriver = webdriver
    
    def setWidth(this, width):
        this.setFixedWidth(width)

    def setHeight(this, height):
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
            print(button.getPos(), button.pos(), button.getParentPos())
            print(this.getPos(), this.getWidth(), this.getHeight())
    
    def setProjectorInterface(this, projectorInterface):
        this.__projectorInterface = projectorInterface
    
    def receive(this, data):
        this.addToBacklog(data)
        if not this.__isProcessingBacklog:
            asyncio.create_task(this.processBacklog())
    
    def getNextFromBacklog(this):
        next = this.__backlog[0]
        del this.__backlog[0]
        return next
    
    def addToBacklog(this, data):
        this.__backlog.append(data)
    
    async def processBacklog(this):
        this.__isProcessingBacklog = True
        while len(this.__backlog) > 0:
            
            data = this.getNextFromBacklog()
            if data == INPUT.POWER:
                await this.powerOff()
            elif data == INPUT.SELECT:
                await this.select()
            elif isinstance(data, str) and data.startswith(INPUT.NAV_PREFIX):
                await this.navigate(data)
            elif data == INPUT.RETURN:
                await this.back()
            elif data == INPUT.VOL_UP:
                await this.volUp()
            elif data == INPUT.VOL_DOWN:
                await this.volDown()
            elif data == INPUT.HOME:
                await this.home()
        
        this.__isProcessingBacklog = False
    
    async def powerOff(this):
        await this.getProjectorInterface().off()
        QCoreApplication.quit()
    
    async def select(this):
        if this.inProjectorMode():
            await this.getProjectorInterface().select()
        else:
            selectedButton = this.getSelectedButton()
            if selectedButton is not None:
                await selectedButton.click()
                if this.inWebMode() and not isinstance(selectedButton, Button):
                    driver = this.getWebDriver()
                    if not driver.elementExists(selectedButton):
                        this.setSelectedButton(driver.getDefaultElement())
            else:
                print("No initial selected button set.")
    
    async def navigate(this, index:str = INPUT.NAV_RIGHT):
        if this.inProjectorMode():
            if index == INPUT.NAV_UP:
                await this.getProjectorInterface().navUp()
            elif index == INPUT.NAV_RIGHT:
                await this.getProjectorInterface().navRight()
            elif index == INPUT.NAV_DOWN:
                await this.getProjectorInterface().navDown()
            elif index == INPUT.NAV_LEFT:
                await this.getProjectorInterface().navLeft()
        elif not this.inOtherMode():
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
    
    async def navUp(this):
        await this.navigate(INPUT.NAV_UP)
    
    async def navRight(this):
        await this.navigate(INPUT.NAV_RIGHT)
    
    async def navDown(this):
        await this.navigate(INPUT.NAV_DOWN)
    
    async def navLeft(this):
        await this.navigate(INPUT.NAV_LEFT)
    
    async def back(this):
        if this.inProjectorMode():
            await this.getProjectorInterface().back()
        elif this.inWebMode():
            this.getWebDriver().quit()
    
    async def volUp(this):
        await this.getProjectorInterface().volUp()
    
    async def volDown(this):
        await this.getProjectorInterface().volDown()
    
    async def home(this):
        if this.inOtherMode():
            await this.switchProjectorInputChannel(PROJECTOR.CHANNELS.HDMI)
        this.setMode(INPUT.MODES.GUI)
        if this.inProjectorMode():
            await this.getProjectorInterface().menu()
        await this.getProjectorInterface().back()
    
    async def openProjectorMenu(this):
        this.setMode(INPUT.MODES.PROJECTOR)
        await this.getProjectorInterface().menu()
    
    async def switchProjectorInputChannel(this, inputChannel):
        if inputChannel != PROJECTOR.CHANNELS.HDMI:
            this.setMode(INPUT.MODES.OTHER)
        await this.getProjectorInterface().switchInputChannel(inputChannel)
    
    def paintEvent(this, event=None):
        painter = QtGui.QPainter()
        painter.begin(this)
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        painter.setPen(QtGui.QPen(GUI.INPUT_INTERFACE_COLOR, 5, Qt.SolidLine))
        painter.drawRect(0, 0, this.getWidth(), this.getHeight())
        
        painter.restore()
        painter.end()

inputInterface = InputInterface()