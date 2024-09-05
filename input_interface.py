print("Importing input interface...")

from globals import INPUT

from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QPoint

class InputInterface(QLabel):
    def __init__(this, selectedButton = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.setWidth(0)
        this.setHeight(0)
        this.setPos(QPoint(0, 0))
        this.setSelectedButton(selectedButton)
        
        this.setWindowFlags(Qt.FramelessWindowHint)
        this.setAttribute(Qt.WA_TranslucentBackground)
        
    def getWidth(this):
        return this.__width

    def getHeight(this):
        return this.__height
    
    def getPos(this):
        return this.__pos
        
    def getSelectedButton(this):
        return this.__selectedButton
    
    def setWidth(this, width):
        this.__width = width
        this.setFixedWidth(width)

    def setHeight(this, height):
        this.__height = height
        this.setFixedWidth(height)
        
    def setPos(this, pos):
        this.__pos = pos
        this.move(pos)
    
    def setSelectedButton(this, button):
        this.__selectedButton = button
        if button != None:
            this.setWidth(button.getWidth())
            this.setHeight(button.getHeight())
            this.setPos(button.getPos())
            print(this.getPos(), this.getWidth(), this.getHeight())
            
    def setParent(this, *args, **kwargs):
        super().setParent(*args, **kwargs)
        
    def receive(this, data):
        if data == INPUT.SELECT:
            this.select()
        elif type(data) == str and data.startswith(INPUT.NAV_PREFIX):
            this.navigate(data)
        
    def select(this):
        selectedButton = this.getSelectedButton()
        if selectedButton != None:
            selectedButton.activate()
        else:
            print("No initial selected button set.")
        
    def navigate(this, index:str = INPUT.NAV_RIGHT):
        selectedButton = this.getSelectedButton()
        if selectedButton != None:
            newButton = selectedButton.getNavButton(index)
            if newButton != None:
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
    
    def paintEvent(this, event):
        painter = QtGui.QPainter()
        painter.begin(this)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        painter.setPen(QtGui.QPen(Qt.red,  5, Qt.SolidLine))
        painter.drawRect(0, 0, this.getWidth(), this.getHeight())
        
        painter.end()
    
inputInterface = InputInterface()