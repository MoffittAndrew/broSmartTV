from button import Button
from tilegrid import tileGrid

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
        
        for button in this.getButtons():
            layout.addWidget(button)
        
        this.setLayout(layout)
        
    def setCurrentButton(this, button):
        this.__currentButton = button
        
    def setTab(this, index):
        this.setCurrentButton(this.getButtons()[index])

class HomeBody(QWidget):
    def __init__(this, widgets:list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.__layout = QStackedLayout()
        
        for widget in widgets:
            this.__layout.addWidget(widget)
        
        this.setLayout(this.__layout)
    
    def setTab(this, index):
        this.__layout.setCurrentIndex(index)
    

class HomeScreen(QWidget):
    def __init__(this, navBar:NavBar, body:HomeBody, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout()
        
        this.__navBar = navBar
        this.__body = body
        layout.addWidget(this.__navBar)
        layout.addWidget(this.__body)
        
        this.setLayout(layout)
        for i in range(len(_buttons)):
            if _buttons[i] == homeButton:
                this.setTab(i)
        
    def setTab(this, index):
        this.__navBar.setTab(index)
        this.__body.setTab(index)
        
navBar = NavBar()
body = HomeBody([tileGrid])

homeScreen = HomeScreen(navBar, body)