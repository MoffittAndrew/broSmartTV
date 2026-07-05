print("Importing infrared interface...")

import os

from globals import DEVICE

class IRInterface:
    def __init__(self, *args, **kwargs):
        self._can_send_ir = DEVICE.IS_RASPBERRY_PI
    
    def send(self, data):
        if self._can_send_ir:
            os.system(f"irsend SEND_ONCE Projector {data}")

irInterface = IRInterface()