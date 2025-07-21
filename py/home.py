print("Importing home screen...")

from globals import GUI, DISPLAY
from button import NavBarButton
from gui import CustomQWidget
from tilegrid import tileGrid
from settings_screen import settingsScreen
from search_screen import searchScreen
from filter_screen import filterScreen
from edit_screen import editScreen

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
    def __init__(this, buttons:list = _buttons, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.setButtons(buttons)
    
    ## Getters
    
    def getButtons(this):
        return this.__buttons
    
    def getCurrentButton(this):
        return this.__currentButton
    
    ## Setters
    
    def setButtons(this, buttons: list[NavBarButton]):
        
        if len(buttons) > 0:
            for i in range(len(buttons) - 1):
                buttons[i + 1].setNavLeft(buttons[i])
                buttons[i].setNavRight(buttons[i + 1])
        
        this.__buttons = buttons
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        for button in this.getButtons():
            layout.addWidget(button)
        
        this.setFixedWidth(len(buttons) * GUI.NAVBAR.BUTTON_WIDTH)
        this.setFixedHeight(GUI.NAVBAR.BUTTON_HEIGHT)
        this.setLayout(layout)
    
    def setCurrentButton(this, button):
        this.__currentButton = button
    
    def setTab(this, index):
        this.setCurrentButton(this.getButtons()[index])
    
    def setPrimaryButton(this, primaryButton):
        for button in this.getButtons():
            button.setNavDown(primaryButton)

class HomeBody(CustomQWidget):
    def __init__(this, widgets:list = _bodyWidgets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.__layout = QStackedLayout()
        this.__layout.setContentsMargins(0, 0, 0, 0)
        
        this.setWidgets(widgets)
    
    def getPrimaryButton(this):
        return this.__layout.currentWidget().getPrimaryButton()
    
    def getWidgets(this):
        return this.__widgets
    
    def getTab(this):
        return this.__tab
    
    def setWidgets(this, widgets):
        this.__widgets = widgets
        for widget in this.getWidgets():
            this.__layout.addWidget(widget)
        
        this.setFixedWidth(DISPLAY.WIDTH)
        this.setLayout(this.__layout)
    
    def setTab(this, index):
        this.__tab = index
        this.__layout.setCurrentIndex(this.getTab())


class HomeScreen(CustomQWidget):
    def __init__(this, navBar:NavBar, body:HomeBody, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.__navBar = navBar
        this.__body = body

        this.__body.setFixedHeight(DISPLAY.HEIGHT - this.__navBar.height())
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(this.__navBar)
        layout.addWidget(this.__body)
        
        this.setFixedHeight(DISPLAY.HEIGHT)
        this.setFixedWidth(DISPLAY.WIDTH)
        this.setLayout(layout)
        
        for i in range(len(_buttons)):
            if _buttons[i].equals(homeButton):
                this.setTab(i)
    
    def getPrimaryButton(this):
        return this.__body.getPrimaryButton()
    
    def setTab(this, index):
        this.__navBar.setTab(index)
        this.__body.setTab(index)
        
        this.__navBar.setPrimaryButton(this.getPrimaryButton())
    
    async def asyncSetTab(this, index):
        this.setTab(index)

navBar = NavBar()
body = HomeBody()

homeScreen = HomeScreen(navBar, body)

for i in range(len(_buttons)):
    _buttons[i].setCallback(homeScreen.asyncSetTab, i)