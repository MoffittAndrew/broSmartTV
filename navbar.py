from PyQt5 import QtWidgets
from button import Button

buttons = [
    Button(text = "home"),
    Button(text = "search"),
    Button(text = "filter"),
    Button(text = "edit"),
    Button(text = "settings"),
]

class NavBar(QtWidgets.QtWidget):
    def __init__(this, buttons:list = buttons, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        this.setButtons(buttons)
        
        layout = QtWidgets.QHBoxLayout()
        
        for button in this.getButtons():
            layout.addWidget(button)
        
        this.setLayout(layout)
        
    ## Getters
        
    def getButtons(this):
        return this.__buttons
    
    def getCurrentButton(this):
        return this.__currentButton
    
    ## Setters
    
    def setButtons(this, buttons):
        this.__buttons = buttons
        this.setCurrentButtons(this.getButtons()[0])
        
    def setCurrentButton(this, button):
        this.__currentButton = button
        
navBar = NavBar()