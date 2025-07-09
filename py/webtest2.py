from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

chrome_options = webdriver.ChromeOptions()
s=Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s,options=chrome_options)
driver.get("http://www.netflix.com")
original_window = driver.current_window_handle
print(original_window)
input()