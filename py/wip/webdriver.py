print("Importing webdriver API...")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.relative_locator import locate_with
from webdriver_manager.chrome import ChromeDriverManager

class WebDriver(webdriver.Chrome):
    def __init__(this, url, incognito = False, *args, **kwargs):
        this.__url = url
        this.__options = Options()
        this.__options.add_experimental_option("useAutomationExtension", False)
        this.__options.add_experimental_option("excludeSwitches",["enable-automation"])
        this.__options.add_argument("--kiosk")
        this.__options.add_argument(f"--app={this.__url}")
        if incognito:
            this.__options.add_argument("--incognito")
        
        this.__service=Service(ChromeDriverManager().install())
        super().__init__(service=this.__service,options=this.__options)
        
    def getDefaultElement(this):
        return this.find_elements(By.TAG_NAME, "button")[0]
    
    def getElementAbove(this, refElement):
        return locate_with(By.TAG_NAME, "button").above(refElement)
    
    def getElementRight(this, refElement):
        return locate_with(By.TAG_NAME, "button").to_right_of(refElement)
    
    def getElementBelow(this, refElement):
        return locate_with(By.TAG_NAME, "button").below(refElement)
    
    def getElementLeft(this, refElement):
        return locate_with(By.TAG_NAME, "button").to_left_of(refElement)
    
    def elementExists(this, element):
        try:
            this.find_element(By.ID, element.get_attribute("id"))
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
    
    def start(this):
        this.get(this.__url)
        
    def quit(this):
        super().quit()
        
        ## TODO go back to home screen