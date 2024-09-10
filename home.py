print("Importing home screen...")

from button import Button
from settings_screen import settingsScreen
from search_screen import searchScreen
from tilegrid import tileGrid
from filter_screen import filterScreen
from edit_screen import editScreen

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout

settingsButton = Button(text = "settings")
searchButton = Button(text = "search")
homeButton = Button(text = "home")
filterButton = Button(text = "filter")
editButton = Button(text = "edit")

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

class NavBar(QWidget):
    def __init__(this, buttons:list = _buttons, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.setButtons(buttons)
        
    ## Getters
        
    def getButtons(this):
        return this.__buttons
    
    def getCurrentButton(this):
        return this.__currentButton
    
    ## Setters
    
    def setButtons(this, buttons):
        
        if len(buttons) > 0:
            for i in range(len(buttons) - 1):
                buttons[i + 1].setNavLeft(buttons[i])
                buttons[i].setNavRight(buttons[i + 1])
                
        this.__buttons = buttons
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        for button in this.getButtons():
            layout.addWidget(button)
        
        this.setLayout(layout)
        
    def setCurrentButton(this, button):
        this.__currentButton = button
        
    def setTab(this, index):
        this.setCurrentButton(this.getButtons()[index])
        
    def setPrimaryButton(this, primaryButton):
        for button in this.getButtons():
            button.setNavDown(primaryButton)
            
    def updateChildPos(this):
        for button in this.getButtons():
            button.setParentPos(this.pos())

class HomeBody(QWidget):
    def __init__(this, widgets:list = _bodyWidgets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.__layout = QStackedLayout()
        this.__layout.setContentsMargins(0, 0, 0, 0)
        
        this.setWidgets(widgets)
        for widget in this.getWidgets():
            this.__layout.addWidget(widget)
        
        this.setLayout(this.__layout)
        
        for button in navBar.getButtons():
            button.setParentPos(navBar.pos())
    
    def getPrimaryButton(this):
        return this.__layout.currentWidget().getPrimaryButton()
        
    def getWidgets(this):
        return this.__widgets
    
    def getTab(this):
        return this.__tab
    
    def setWidgets(this, widgets):
        this.__widgets = widgets
    
    def setTab(this, index):
        this.__tab = index
        this.__layout.setCurrentIndex(this.getTab())
        
    def updateChildPos(this):
        for widget in this.getWidgets():
            widget.updateChildPos()
    

class HomeScreen(QWidget):
    def __init__(this, navBar:NavBar, body:HomeBody, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        this.__navBar = navBar
        this.__body = body
        layout.addWidget(this.getNavBar())
        layout.addWidget(this.getBody())
        
        this.setLayout(layout)
        for i in range(len(_buttons)):
            if _buttons[i].equals(homeButton):
                this.setTab(i)
        
    def getNavBar(this):
        return this.__navBar
    
    def getBody(this):
        return this.__body
                
    def getPrimaryButton(this):
        return this.__body.getPrimaryButton()
        
    def setTab(this, index):
        this.getNavBar().setTab(index)
        this.getBody().setTab(index)
        
        this.getNavBar().setPrimaryButton(this.getPrimaryButton())
        
    def show(this, *args, **kwargs):
        super().show(*args, **kwargs)
        this.getNavBar().updateChildPos() 
        this.getBody().updateChildPos()
        
navBar = NavBar()
body = HomeBody()

homeScreen = HomeScreen(navBar, body)

for i in range(len(_buttons)):
    _buttons[i].setCallback(homeScreen.setTab, i)