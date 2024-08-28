import os

PATH = os.path.dirname(__file__) + "\\..\\"

class BUTTON:
    MIN_HEIGHT = 10
    MIN_WIDTH = 10

class TILE:
    WIDTH = 100
    HEIGHT = 100
    EDIT_NAME_TEXT = "edit url"
    EDIT_IMG_TEXT = "edit image"
    EDIT_INPUT_TEXT = "edit input channel"
    EDIT_URL_TEXT = "edit url"
    TOGGLE_MUSIC_TEXT = "music site?"
    TOGGLE_SEARCH_TEXT = "has search feature?"
    TOGGLE_PIRATE_TEXT = "pirate site?"

class REMOTE:
    NAME = "bro-ito"
    SERVICE_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x1849)
    CHARACTERISTIC_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2BA5)
    BUTTONS = [
        "HOME",
        "POWER",
        "SELECT",
        "NAV_UP",
        "NAV_RIGHT",
        "NAV_DOWN",
        "NAV_LEFT",
        "MENU",
        "RETURN",
        "VOL_UP",
        "VOL_DOWN",
        "MIC",
    ]