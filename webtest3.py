from PyQt5 import QtCore, QtGui, QtWidgets
import win32gui
import win32con
import winxpgui
import win32api
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import ctypes
user32 = ctypes.windll.user32
width,height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

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
        this.frame = QtWidgets.QFrame(this.centralwidget)
        this.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        this.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        this.frame.setObjectName("frame")
        #this.verticalLayout.addWidget(this.frame)
        MainWindow.setCentralWidget(this.centralwidget)
        
        
        this.chrome_options = Options()
        this.chrome_options.add_argument("disable-infobars")
        #this.chrome_options.add_argument("--window-size=0,0")
        this.chrome_options.add_argument("--kiosk")
        this.chrome_options.add_argument("--window-size="+str(int(2*width))+","+str(int(2*height)))
        this.chrome_options.add_argument("--window-position=-10,-10")
        this.chrome_options.add_argument(f"--app={url}"); 
        this.s=Service(ChromeDriverManager().install())
        
        this.driver = webdriver.Chrome(service=this.s,options=this.chrome_options)
        this.driver.get(url)
        time.sleep(0.5)
        

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
                this.tries+= 1
                break
                time.sleep(1)
            except Exception as e:
                print(e)
                this.tries += 1
                
                
        this.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
            
    def hwnd_method(this, hwnd, ctx):
        window_title = win32gui.GetWindowText(hwnd)
        if "netflix" in window_title.lower():
            this.hwnd = hwnd
            '''        
            old_style = win32gui.GetWindowLong(hwnd, -16)
            # building the new style(old style AND NOT Maximize AND NOT Minimize)
            new_style = old_style & ~win32con.WS_MAXIMIZEBOX & ~win32con.WS_MINIMIZEBOX
            # setting new style
            win32gui.SetWindowLong(hwnd, -16, new_style)
            # updating non - client area
            win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
            win32gui.UpdateWindow(hwnd)
            '''
            #win32gui.ShowWindow(hwnd , win32con.SW_HIDE)
            
            #win32gui.SetWindowLong (hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong (hwnd, win32con.GWL_EXSTYLE ) | win32con.WS_EX_LAYERED )
            #winxpgui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0,0,0), 0, win32con.LWA_ALPHA)

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