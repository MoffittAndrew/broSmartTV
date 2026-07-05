print("Importing home screen...")

from globals import GUI, DISPLAY
from ui.gui import CustomQWidget
from ui.tools.button import NavBarButton
from ui.tools.tilegrid import tileGrid
from ui.settings_screen import settingsScreen
from ui.search_screen import searchScreen
from ui.filter_screen import filterScreen
from ui.edit_screen import editScreen

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QStackedLayout

settingsButton = NavBarButton(text = "settings")
searchButton = NavBarButton(text = "search")
homeButton = NavBarButton(text = "home")
filterButton = NavBarButton(text = "filter")
editButton = NavBarButton(text = "edit")

_buttons = [
    settingsButton,
    searchButton,
    homeButton,
    filterButton,
    editButton,
]

_bodyWidgets = [
    settingsScreen,
    searchScreen,
    tileGrid,
    filterScreen,
    editScreen,
]


tileGrid.setNavBarButton(homeButton)

class NavBar(CustomQWidget):
    def __init__(self, buttons:list = _buttons, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setButtons(buttons)
    
    ## Getters
    
    def getButtons(self):
        return self.__buttons
    
    def getCurrentButton(self):
        return self.__currentButton
    
    ## Setters
    
    def setButtons(self, buttons: list[NavBarButton]):
        
        if len(buttons) > 0:
            for i in range(len(buttons) - 1):
                buttons[i + 1].setNavLeft(buttons[i])
                buttons[i].setNavRight(buttons[i + 1])
        
        self.__buttons = buttons
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        for button in self.getButtons():
            layout.addWidget(button)
        
        self.setFixedWidth(len(buttons) * GUI.NAVBAR.BUTTON_WIDTH)
        self.setFixedHeight(GUI.NAVBAR.BUTTON_HEIGHT)
        self.setLayout(layout)
    
    def setCurrentButton(self, button):
        self.__currentButton = button
    
    def setTab(self, index):
        self.setCurrentButton(self.getButtons()[index])
    
    def setPrimaryButton(self, primaryButton):
        for button in self.getButtons():
            button.setNavDown(primaryButton)

class HomeBody(CustomQWidget):
    def __init__(self, widgets:list = _bodyWidgets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__layout = QStackedLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        
        self.setWidgets(widgets)
    
    def getPrimaryButton(self):
        return self.__layout.currentWidget().getPrimaryButton()
    
    def getWidgets(self):
        return self.__widgets
    
    def getTab(self):
        return self.__tab
    
    def setWidgets(self, widgets):
        self.__widgets = widgets
        for widget in self.getWidgets():
            self.__layout.addWidget(widget)
        
        self.setFixedWidth(DISPLAY.WIDTH)
        self.setLayout(self.__layout)
    
    def setTab(self, index):
        self.__tab = index
        self.__layout.setCurrentIndex(self.getTab())


class HomeScreen(CustomQWidget):
    def __init__(self, navBar:NavBar, body:HomeBody, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.__navBar = navBar
        self.__body = body

        self.__body.setFixedHeight(DISPLAY.HEIGHT - self.__navBar.height())
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__navBar)
        layout.addWidget(self.__body)
        
        self.setFixedHeight(DISPLAY.HEIGHT)
        self.setFixedWidth(DISPLAY.WIDTH)
        self.setLayout(layout)
        
        for i in range(len(_buttons)):
            if _buttons[i].equals(homeButton):
                self.setDefaultTab(i)
        
        self.setTab()
    
    def getPrimaryButton(self):
        return self.__body.getPrimaryButton()
    
    def getDefaultTab(self):
        return self.__defaultTab
    
    def setDefaultTab(self, tab):
        self.__defaultTab = tab
    
    def setTab(self, index=None):
        if index is None:
            index = self.getDefaultTab()
        
        self.__navBar.setTab(index)
        self.__body.setTab(index)
        
        self.__navBar.setPrimaryButton(self.getPrimaryButton())
    
    async def asyncSetTab(self, index=None):
        self.setTab(index)

navBar = NavBar()
body = HomeBody()

homeScreen = HomeScreen(navBar, body)

for i in range(len(_buttons)):
    _buttons[i].setCallback(homeScreen.asyncSetTab, i)