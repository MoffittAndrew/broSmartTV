#!/usr/bin/env python

from selenium import webdriver
from pyvirtualdisplay import Display

print ('Starting ...')
display = Display(visible=0, size=(1600, 1200))
display.start()
driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
print ('webdriver loaded')

# Navigate to target website
driver.get('https://www.youtube.com')

driver.save_screenshot('SeleniumChromiumTest.png')
print ('target page loaded adnd screenshot taken')
print ('Done')