print("Importing globals...")

import os
from PyQt5.QtCore import Qt

PATH = os.path.dirname(__file__) + "\\..\\"

class DISPLAY:
    WIDTH = 1920
    HEIGHT = 1080

class BUTTON:
    MIN_WIDTH = 200
    MIN_HEIGHT = 100

class TILE:
    WIDTH = 400
    HEIGHT = 300
    EDIT_NAME_TEXT = "edit url"
    EDIT_IMG_TEXT = "edit image"
    EDIT_INPUT_TEXT = "edit input channel"
    EDIT_URL_TEXT = "edit url"
    TOGGLE_MUSIC_TEXT = "music site?"
    TOGGLE_SEARCH_TEXT = "has search feature?"
    TOGGLE_PIRATE_TEXT = "pirate site?"
    
class TILEGRID:
    COLUMNS = 5

class REMOTE:
    NAME = "bro-ito"
    SERVICE_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x1849)
    CHARACTERISTIC_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2BA5)
    CHECK_ALIVE_INTERVAL = 5
    SCAN_TIMEOUT = 30
    
class INPUT:
    RELEASED_PREFIX = "RELEASED_"
    NAV_PREFIX = "NAV_"
    HOME = "HOME"
    POWER = "POWER"
    SELECT = "SELECT"
    NAV_UP = NAV_PREFIX + "UP"
    NAV_RIGHT = NAV_PREFIX + "RIGHT"
    NAV_DOWN = NAV_PREFIX + "DOWN"
    NAV_LEFT = NAV_PREFIX + "LEFT"
    MENU = "MENU"
    RETURN = "RETURN"
    VOL_UP = "VOL_UP"
    VOL_DOWN = "VOL_DOWN"
    MIC = "MIC"
    LOOKUP = {
        SELECT: Qt.Key_Return,
        NAV_UP: Qt.Key_Up,
        NAV_RIGHT: Qt.Key_Right,
        NAV_DOWN: Qt.Key_Down,
        NAV_LEFT: Qt.Key_Left,
    }
    
class WEB:
    CHROMIUM_PATH = "/usr/lib/chromium-browser/chromedriver"
    MAX_GET_WINDOW_TRIES = 30