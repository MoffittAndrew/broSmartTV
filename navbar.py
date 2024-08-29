from button import Button

from PyQt5.QtWidgets import QWidget, QHBoxLayout

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
        this.setCurrentButton(homeButton)
        
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
    
    ## Other
    
    def draw(this):
        for button in this.getButtons():
            button.draw()
        
navBar = NavBar()