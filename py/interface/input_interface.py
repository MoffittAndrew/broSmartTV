print("Importing input interface...")

from globals import INPUT, GUI, PROJECTOR
from ui.tools.button import Button
from ui.gui import MAIN_WINDOW, CustomQLabel

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea

import asyncio
from teardown import teardown_app

class InputInterface(CustomQLabel):
    def __init__(self, selectedButton = None, projectorInterface = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__mode = INPUT.MODES.GUI
        self.setOldMode(INPUT.MODES.GUI)
        self.setSelectedButton(selectedButton)
        self.setRoundness(GUI.BUTTON.ROUNDNESS)
        self.setBorderThickness(GUI.BUTTON.BORDER_THICKNESS)
        self.setProjectorInterface(projectorInterface)
        self.__backlog = []
        self.__isProcessingBacklog = False
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
    
    def inGUIMode(self):
        return self.getMode() == INPUT.MODES.GUI
    
    def inProjectorMode(self):
        return self.getMode() == INPUT.MODES.PROJECTOR

    def inWebMode(self):
        return self.getMode() == INPUT.MODES.WEB

    def inOtherMode(self):
        return self.getMode() == INPUT.MODES.OTHER
    
    def getMode(self):
        return self.__mode

    def getOldMode(self):
        return self.__oldMode

    def getWebDriver(self):
        return self.__webdriver
    
    def getSelectedButton(self):
        return self.__selectedButton
    
    def getRoundness(self):
        return self.__roundness
    
    def getBorderThickness(self):
        return self.__borderThickness

    def getProjectorInterface(self):
        return self.__projectorInterface
    
    def setMode(self, mode = INPUT.MODES.GUI):
        if mode == INPUT.MODES.PROJECTOR and self.getProjectorInterface() is None:
            print("Cannot set input interface to projector mode, no projector interface has been set!")
        elif self.getMode() != mode:
            self.setOldMode(self.getMode())
            self.__mode = mode
    
    def setOldMode(self, oldMode):
        self.__oldMode = oldMode
    
    def setWebDriver(self, webdriver):
        self.__webdriver = webdriver
    
    def setSelectedButton(self, button):
        self.__selectedButton = button
        if button is not None:
            if isinstance(button, Button):
                width = button.width()
                height = button.height()
                pos = button.getAbsolutePos()
                x, y = (pos.x(), pos.y())
                roundness = button.getRoundness()
                borderThickness = button.getBorderThickness()
                self._scrollButtonIntoView(button)
            else:
                rect = button.rect
                width = rect["width"]
                height = rect["height"]
                x, y = (int(rect["x"]), int(rect["y"]))
                roundness = 0
                borderThickness = 2
            
            self.setRoundness(roundness)
            self.setBorderThickness(borderThickness)
            self.setGeometry(x, y, width, height)
            # Keep the selection outline above active UI layers (e.g. keyboard overlay).
            self.show()
            self.raise_()
            self.update()

    def _findParentScrollArea(self, widget):
        parent = widget.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                return parent
            parent = parent.parent()
        return None

    def _scrollButtonIntoView(self, button):
        scrollArea = self._findParentScrollArea(button)
        if scrollArea is not None:
            scrollArea.ensureWidgetVisible(button, 40, 40)
    
    def setRoundness(self, roundness):
        self.__roundness = roundness
    
    def setBorderThickness(self, borderThickness):
        self.__borderThickness = borderThickness
    
    def setProjectorInterface(self, projectorInterface):
        self.__projectorInterface = projectorInterface
    
    def receive(self, data):
        self.addToBacklog(data)
        if not self.__isProcessingBacklog:
            asyncio.create_task(self.processBacklog())
        else:
            print(f"{data} added to backlog, as we are still processing previous inputs.")
    
    def getNextFromBacklog(self):
        next = self.__backlog[0]
        del self.__backlog[0]
        return next
    
    def addToBacklog(self, data):
        self.__backlog.append(data)
    
    async def processBacklog(self):
        self.__isProcessingBacklog = True
        try:
            while len(self.__backlog) > 0:

                data = self.getNextFromBacklog()
                try:
                    if data == INPUT.RELEASED_PREFIX + INPUT.POWER:
                        await self.powerOff()
                    elif data == INPUT.RELEASED_PREFIX + INPUT.SELECT:
                        await self.select()
                    elif isinstance(data, str) and data.startswith(INPUT.NAV_PREFIX):
                        await self.navigate(data)
                    elif data == INPUT.RELEASED_PREFIX + INPUT.RETURN:
                        await self.back()
                    elif data == INPUT.RELEASED_PREFIX + INPUT.MENU:
                        await self.menu()
                    elif data == INPUT.VOL_UP:
                        await self.volUp()
                    elif data == INPUT.VOL_DOWN:
                        await self.volDown()
                    elif data == INPUT.RELEASED_PREFIX + INPUT.HOME:
                        await self.home()
                except Exception as error:
                    print(f"Error while handling input '{data}': {error}")
        finally:
            self.__isProcessingBacklog = False
    
    async def powerOff(self):
        await teardown_app(projector_interface=self.getProjectorInterface(), quit_app=True)
    
    async def select(self):
        if self.inProjectorMode():
            await self.getProjectorInterface().select()
        else:
            selectedButton = self.getSelectedButton()
            if selectedButton is not None:
                await selectedButton.click()
                if self.inWebMode() and not isinstance(selectedButton, Button):
                    driver = self.getWebDriver()
                    if not driver.elementExists(selectedButton):
                        self.setSelectedButton(driver.getDefaultElement())
            else:
                print("No initial selected button set.")
    
    async def navigate(self, index:str = INPUT.NAV_RIGHT):
        if self.inProjectorMode():
            if index == INPUT.NAV_UP:
                await self.getProjectorInterface().navUp()
            elif index == INPUT.NAV_RIGHT:
                await self.getProjectorInterface().navRight()
            elif index == INPUT.NAV_DOWN:
                await self.getProjectorInterface().navDown()
            elif index == INPUT.NAV_LEFT:
                await self.getProjectorInterface().navLeft()
        elif not self.inOtherMode():
            selectedButton = self.getSelectedButton()
            if selectedButton is not None:
                if not self.inWebMode():
                    newButton = selectedButton.getNavButton(index)
                
                else:
                    driver = self.getWebDriver()
                    if driver is not None:
                        if index == INPUT.NAV_UP:
                            newButtonLocator = driver.getElementAbove(selectedButton)
                        elif index == INPUT.NAV_RIGHT:
                            newButtonLocator = driver.getElementRight(selectedButton)
                        elif index == INPUT.NAV_DOWN:
                            newButtonLocator = driver.getElementBelow(selectedButton)
                        elif index == INPUT.NAV_LEFT:
                            newButtonLocator = driver.getElementLeft(selectedButton)
                        else:
                            newButtonLocator = None
                        newButton = driver.find_element(newButtonLocator)
                    else:
                        print("No webdriver set!")
                        newButton = None
                
                if newButton is not None:
                    self.setSelectedButton(newButton)
            else:
                print("No initial selected button set.")
    
    async def navUp(self):
        await self.navigate(INPUT.NAV_UP)
    
    async def navRight(self):
        await self.navigate(INPUT.NAV_RIGHT)
    
    async def navDown(self):
        await self.navigate(INPUT.NAV_DOWN)
    
    async def navLeft(self):
        await self.navigate(INPUT.NAV_LEFT)
    
    async def back(self):
        if self.inProjectorMode():
            await self.getProjectorInterface().back()
        elif self.inWebMode():
            self.getWebDriver().quit()
    
    async def menu(self):
        if self.inGUIMode():
            self.getSelectedButton().openMenu()
    
    async def volUp(self):
        await self.getProjectorInterface().volUp()
        if self.inProjectorMode():
            self.setMode(self.getOldMode())
    
    async def volDown(self):
        await self.getProjectorInterface().volDown()
        if self.inProjectorMode():
            self.setMode(self.getOldMode())
    
    async def home(self):
        if self.inOtherMode():
            await self.switchProjectorInputChannel(PROJECTOR.CHANNELS.HDMI)
        if self.inProjectorMode():
            await self.getProjectorInterface().menu()
        else:
            MAIN_WINDOW.setTab()
        self.setMode(INPUT.MODES.GUI)
        await self.getProjectorInterface().back()
    
    async def openProjectorMenu(self):
        self.setMode(INPUT.MODES.PROJECTOR)
        await self.getProjectorInterface().menu()
    
    async def switchProjectorInputChannel(self, inputChannel):
        if inputChannel != PROJECTOR.CHANNELS.HDMI:
            self.setMode(INPUT.MODES.OTHER)
        await self.getProjectorInterface().switchInputChannel(inputChannel)
    
    def paintEvent(self, event=None):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        painter.setPen(QtGui.QPen(GUI.INPUT_INTERFACE_COLOR, self.getBorderThickness(), Qt.SolidLine))
        painter.drawRoundedRect(
            int(self.getBorderThickness()/2),
            int(self.getBorderThickness()/2),
            self.width() - self.getBorderThickness(),
            self.height() - self.getBorderThickness(),
            self.getRoundness(),
            self.getRoundness(),
        )
        
        painter.restore()
        painter.end()

inputInterface = InputInterface()