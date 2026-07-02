print("Importing infrared interface...")

import os

class IRInterface:
    def __init__(self, *args, **kwargs):
        ...
    
    def send(self, data):
        os.system(f"irsend SEND_ONCE Projector {data}")

irInterface = IRInterface()