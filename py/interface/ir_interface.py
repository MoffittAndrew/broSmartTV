print("Importing infrared interface...")

import os

class IRInterface:
    def __init__(this, *args, **kwargs):
        ...
    
    def send(this, data):
        os.system(f"sudo irsend SEND_ONCE Epson_12807990 {data}")

irInterface = IRInterface()