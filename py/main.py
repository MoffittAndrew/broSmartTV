print("Starting...")

print("Starting imports...")
from gui import MAIN_WINDOW
from input_interface import inputInterface
#from web_interface import webInterface
from home import homeScreen
from remote import remote
from keyboard import keyboard

print("Completed imports.")

MAIN_WINDOW.setInputInterface(inputInterface)
MAIN_WINDOW.addWidget(homeScreen)
#MAIN_WINDOW.addWidget(webInterface)

keyboard.setInputInterface(inputInterface)
remote.setInputInterface(inputInterface)
MAIN_WINDOW.setKeyboard(keyboard)

MAIN_WINDOW.setTab(homeScreen)