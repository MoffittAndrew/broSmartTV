from PyQt5 import QtCore, QtGui, QtWidgets
import win32gui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

url="http://www.netflix.com"


class Ui_MainWindow(object):
    def setupUi(this, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        this.centralwidget = QtWidgets.QWidget(MainWindow)
        this.centralwidget.setObjectName("centralwidget")
        this.verticalLayout = QtWidgets.QVBoxLayout(this.centralwidget)
        this.verticalLayout.setContentsMargins(0, 0, 0, 0)
        this.verticalLayout.setObjectName("verticalLayout")
        MainWindow.setCentralWidget(this.centralwidget)
        
        
        this.chrome_options = Options()
        this.chrome_options.add_experimental_option("useAutomationExtension", False)
        this.chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
        this.chrome_options.add_argument("--kiosk")
        this.chrome_options.add_argument(f"--app={url}")
        this.s=Service(ChromeDriverManager().install())
        
        this.driver = webdriver.Chrome(service=this.s,options=this.chrome_options)
        time.sleep(0.2)

        this.hwnd = 0
        this.tries = 30
        this.total_tries = 0
        while(this.hwnd==0 and this.total_tries<=this.tries):
            try:
                win32gui.EnumWindows(this.hwnd_method, None)
                #win32gui.SetWindowLong (this.hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong (this.hwnd, win32con.GWL_EXSTYLE ) | win32con.WS_EX_LAYERED )
                #winxpgui.SetLayeredWindowAttributes(this.hwnd, win32api.RGB(0,0,0), 255, win32con.LWA_ALPHA)
                this.embed_window = QtGui.QWindow.fromWinId(this.hwnd)
                this.embed_widget = QtWidgets.QWidget.createWindowContainer(this.embed_window)
                this.verticalLayout.addWidget(this.embed_widget)
                #this.driver.execute_script("document.documentElement.requestFullscreen();")
                this.tries += 1
                break
            except Exception as e:
                print(e)
                this.tries += 1
                
                
        this.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        this.driver.get(url)
            
    def hwnd_method(this, hwnd, ctx):
        window_title = win32gui.GetWindowText(hwnd)
        print(window_title)
        if "netflix" in window_title.lower():
            this.hwnd = hwnd

    def retranslateUi(this, MainWindow):
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