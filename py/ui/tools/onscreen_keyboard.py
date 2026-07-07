print("Importing onscreen keyboard...")

from ui.tools.button import Button, ToggleButton
from ui.gui import CustomQWidget

class OnScreenKeyboard(CustomQWidget):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
    
    def getPrimaryButton(self):
        ...

onScreenKeyboard = OnScreenKeyboard()