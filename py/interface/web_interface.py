print("Importing web interface...")

from globals import WEB
from webdriver import WebDriver

from win32gui import EnumWindows, GetWindowText
from time import sleep
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QWindow

class WebInterface(QWidget):
    def __init__(this, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this.__max_tries = WEB.MAX_GET_WINDOW_TRIES
        this.__layout = QVBoxLayout(this)
        this.__layout.setContentsMargins(0, 0, 0, 0)
        
    def openURL(this, url, incognito = False):
        
        this.__url = url
        this.__driver = WebDriver(url, incognito)
        sleep(0.5)

        this.__hwnd = 0
        this.__tries = 0
        while this.__hwnd == 0 and this.__tries <= this.__max_tries:
            try:
                EnumWindows(this.hwnd_method, None)
                this.__embed_window = QWindow.fromWinId(this.__hwnd)
                this.__layout.addWidget(QWidget.createWindowContainer(this.__embed_window))
                this.__tries += 1
                break
            except Exception as e:
                print(f"Error: {e}")
                this.__tries += 1
                
        this.__driver.start()
        this.parent().setTab(this)
        this.parent().getInputInterface().setWebMode(webdriver=this.__driver)

    def hwnd_method(this, hwnd, ctx):
        searchtext = this.__url.split(".")[1] ## TODO make better
        #print(searchtext)
        window_title = GetWindowText(hwnd)
        if searchtext in window_title.lower():
            this.__hwnd = hwnd
    
    def getPrimaryButton(this):
        return this.__driver.getDefaultElement()

webInterface = WebInterface()