print("Importing web interface...")

from globals import WEB
from webdriver import WebDriver

from win32gui import EnumWindows, GetWindowText
from time import sleep
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QWindow

class WebInterface(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__max_tries = WEB.MAX_GET_WINDOW_TRIES
        self.__layout = QVBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        
    def openURL(self, url, incognito = False):
        
        self.__url = url
        self.__driver = WebDriver(url, incognito)
        sleep(0.5)

        self.__hwnd = 0
        self.__tries = 0
        while self.__hwnd == 0 and self.__tries <= self.__max_tries:
            try:
                EnumWindows(self.hwnd_method, None)
                self.__embed_window = QWindow.fromWinId(self.__hwnd)
                self.__layout.addWidget(QWidget.createWindowContainer(self.__embed_window))
                self.__tries += 1
                break
            except Exception as e:
                print(f"Error: {e}")
                self.__tries += 1
                
        self.__driver.start()
        self.parent().setTab(self)
        self.parent().getInputInterface().setWebMode(webdriver=self.__driver)

    def hwnd_method(self, hwnd, ctx):
        searchtext = self.__url.split(".")[1] ## TODO make better
        #print(searchtext)
        window_title = GetWindowText(hwnd)
        if searchtext in window_title.lower():
            self.__hwnd = hwnd
    
    def getPrimaryButton(self):
        return self.__driver.getDefaultElement()

webInterface = WebInterface()