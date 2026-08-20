print("Importing webdriver API...")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.relative_locator import locate_with
from webdriver_manager.chrome import ChromeDriverManager

class WebDriver(webdriver.Chrome):
    def __init__(self, url, incognito = False, *args, **kwargs):
        self.__url = url
        self.__options = Options()
        self.__options.add_experimental_option("useAutomationExtension", False)
        self.__options.add_experimental_option("excludeSwitches",["enable-automation"])
        self.__options.add_argument("--kiosk")
        self.__options.add_argument(f"--app={self.__url}")
        if incognito:
            self.__options.add_argument("--incognito")
        
        self.__service=Service(ChromeDriverManager().install())
        super().__init__(service=self.__service,options=self.__options)
        
    def getDefaultElement(self):
        return self.find_elements(By.TAG_NAME, "button")[0]
    
    def getElementAbove(self, refElement):
        return locate_with(By.TAG_NAME, "button").above(refElement)
    
    def getElementRight(self, refElement):
        return locate_with(By.TAG_NAME, "button").to_right_of(refElement)
    
    def getElementBelow(self, refElement):
        return locate_with(By.TAG_NAME, "button").below(refElement)
    
    def getElementLeft(self, refElement):
        return locate_with(By.TAG_NAME, "button").to_left_of(refElement)
    
    def elementExists(self, element):
        try:
            self.find_element(By.ID, element.get_attribute("id"))
        except Exception as e:
            print(f"Element not found: {e}")
            return False
        return True
    
    def find_element(self, by=By.ID, value: str | None = None) -> WebElement:
        element = None
        try:
            element = super().find_element(by, value)
        except Exception as e:
            print(f"Element not found: {e}")
        return element
    
    def start(self):
        self.get(self.__url)
        
    def quit(self):
        super().quit()
        
        ## TODO go back to home screen