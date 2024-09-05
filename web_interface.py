print("Importing web interface...")

from globals import WEB
from gui import MAIN_WINDOW

from win32gui import EnumWindows, GetWindowText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from time import sleep
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QWindow

class WebInterface(QWidget):
    def __init__(this, parent = MAIN_WINDOW, *args, **kwargs):
        super().__init__(parent = parent, *args, **kwargs)
        this.__max_tries = WEB.MAX_GET_WINDOW_TRIES
        this.__layout = QVBoxLayout(this)
        this.__layout.setContentsMargins(0, 0, 0, 0)
        
    def openURL(this, url):
        
        this.__url = url
        this.__options = Options()
        this.__options.add_experimental_option("useAutomationExtension", False)
        this.__options.add_experimental_option("excludeSwitches",["enable-automation"])
        this.__options.add_argument("--kiosk")
        this.__options.add_argument(f"--app={this.__url}")
        this.__service=Service(ChromeDriverManager().install())
        
        this.__driver = webdriver.Chrome(service=this.__service,options=this.__options)
        sleep(1)

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
                print(e)
                this.__tries += 1
                
        this.parent().setTab(1)
        this.__driver.get(this.__url)
            
    def hwnd_method(this, hwnd, ctx):
        searchtext = this.__url.split(".")[1]
        #print(searchtext)
        window_title = GetWindowText(hwnd)
        if searchtext in window_title.lower():
            this.__hwnd = hwnd
        
    def close(this):
        this.__driver.quit()

webInterface = WebInterface()