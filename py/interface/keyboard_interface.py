print("Importing keyboard interface...")

from globals import INPUT

class KeyboardInterface:
    def __init__(this, inputInterface = None):
        this.setInputInterface(inputInterface)
    
    def getInputInterface(this):
        return this.__inputInterface
    
    def setInputInterface(this, inputInterface):
        this.__inputInterface = inputInterface
    
    def receive(this, key, released_prefix = None):
        
        keyStr = None
        for key_lookup in INPUT.LOOKUP:
            if key == INPUT.LOOKUP[key_lookup]:
                keyStr = key_lookup
        
        if keyStr is not None:
            if released_prefix is not None:
                keyStr = released_prefix + keyStr
            
            print(f"Recieved keyboard signal {keyStr}")
            if this.getInputInterface() is not None:
                this.getInputInterface().receive(keyStr)
            else:
                print("Keyboard has no input interface!")

keyboardInterface = KeyboardInterface()