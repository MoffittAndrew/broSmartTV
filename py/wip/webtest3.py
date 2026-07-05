from PyQt5 import QtCore, QtGui, QtWidgets
import win32gui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

url="http://www.netflix.com"


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        MainWindow.setCentralWidget(self.centralwidget)
        
        
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
        self.chrome_options.add_argument("--kiosk")
        self.chrome_options.add_argument(f"--app={url}")
        self.s=Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=self.s,options=self.chrome_options)
        time.sleep(0.2)

        self.hwnd = 0
        self.tries = 30
        self.total_tries = 0
        while(self.hwnd==0 and self.total_tries<=self.tries):
            try:
                win32gui.EnumWindows(self.hwnd_method, None)
                #win32gui.SetWindowLong (self.hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong (self.hwnd, win32con.GWL_EXSTYLE ) | win32con.WS_EX_LAYERED )
                #winxpgui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(0,0,0), 255, win32con.LWA_ALPHA)
                self.embed_window = QtGui.QWindow.fromWinId(self.hwnd)
                self.embed_widget = QtWidgets.QWidget.createWindowContainer(self.embed_window)
                self.verticalLayout.addWidget(self.embed_widget)
                #self.driver.execute_script("document.documentElement.requestFullscreen();")
                self.tries += 1
                break
            except Exception as e:
                print(e)
                self.tries += 1
                
                
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.driver.get(url)
            
    def hwnd_method(self, hwnd, ctx):
        window_title = win32gui.GetWindowText(hwnd)
        print(window_title)
        if "netflix" in window_title.lower():
            self.hwnd = hwnd

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())