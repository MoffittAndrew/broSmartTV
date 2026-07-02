print("Importing input interface...")

from globals import INPUT, GUI, PROJECTOR
from ui.tools.button import Button
from ui.gui import MAIN_WINDOW, CustomQLabel

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QCoreApplication

import asyncio
from screen_cast import stopScreenCastServer

class InputInterface(CustomQLabel):
    def __init__(this, selectedButton = None, projectorInterface = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.__mode = INPUT.MODES.GUI
        this.setOldMode(INPUT.MODES.GUI)
        this.setSelectedButton(selectedButton)
        this.setRoundness(GUI.BUTTON.ROUNDNESS)
        this.setBorderThickness(GUI.BUTTON.BORDER_THICKNESS)
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

    def getOldMode(this):
        return this.__oldMode

    def getWebDriver(this):
        return this.__webdriver
    
    def getSelectedButton(this):
        return this.__selectedButton
    
    def getRoundness(this):
        return this.__roundness
    
    def getBorderThickness(this):
        return this.__borderThickness

    def getProjectorInterface(this):
        return this.__projectorInterface
    
    def setMode(this, mode = INPUT.MODES.GUI):
        if mode == INPUT.MODES.PROJECTOR and this.getProjectorInterface() is None:
            print("Cannot set input interface to projector mode, no projector interface has been set!")
        elif this.getMode() != mode:
            this.setOldMode(this.getMode())
            this.__mode = mode
    
    def setOldMode(this, oldMode):
        this.__oldMode = oldMode
    
    def setWebDriver(this, webdriver):
        this.__webdriver = webdriver
    
    def setSelectedButton(this, button):
        this.__selectedButton = button
        if button is not None:
            if isinstance(button, Button):
                width = button.width()
                height = button.height()
                pos = button.getAbsolutePos()
                x, y = (pos.x(), pos.y())
                roundness = button.getRoundness()
                borderThickness = button.getBorderThickness()
            else:
                rect = button.rect
                width = rect["width"]
                height = rect["height"]
                x, y = (int(rect["x"]), int(rect["y"]))
                roundness = 0
                borderThickness = 2
            
            this.setRoundness(roundness)
            this.setBorderThickness(borderThickness)
            this.setGeometry(x, y, width, height)
    
    def setRoundness(this, roundness):
        this.__roundness = roundness
    
    def setBorderThickness(this, borderThickness):
        this.__borderThickness = borderThickness
    
    def setProjectorInterface(this, projectorInterface):
        this.__projectorInterface = projectorInterface
    
    def receive(this, data):
        this.addToBacklog(data)
        if not this.__isProcessingBacklog:
            asyncio.create_task(this.processBacklog())
        else:
            print(f"{data} added to backlog, as we are still processing previous inputs.")
    
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
            if data == INPUT.RELEASED_PREFIX + INPUT.POWER:
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
            elif data == INPUT.RELEASED_PREFIX + INPUT.HOME:
                await this.home()
        
        this.__isProcessingBacklog = False
    
    async def powerOff(this):
        projectorInterface = this.getProjectorInterface()
        if projectorInterface is not None:
            await projectorInterface.off()

        await stopScreenCastServer()
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
        if this.inProjectorMode():
            this.setMode(this.getOldMode())
    
    async def volDown(this):
        await this.getProjectorInterface().volDown()
        if this.inProjectorMode():
            this.setMode(this.getOldMode())
    
    async def home(this):
        if this.inOtherMode():
            await this.switchProjectorInputChannel(PROJECTOR.CHANNELS.HDMI)
        if this.inProjectorMode():
            await this.getProjectorInterface().menu()
        else:
            MAIN_WINDOW.setTab()
        this.setMode(INPUT.MODES.GUI)
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

        painter.setPen(QtGui.QPen(GUI.INPUT_INTERFACE_COLOR, this.getBorderThickness(), Qt.SolidLine))
        painter.drawRoundedRect(
            int(this.getBorderThickness()/2),
            int(this.getBorderThickness()/2),
            this.width() - this.getBorderThickness(),
            this.height() - this.getBorderThickness(),
            this.getRoundness(),
            this.getRoundness(),
        )
        
        painter.restore()
        painter.end()

inputInterface = InputInterface()