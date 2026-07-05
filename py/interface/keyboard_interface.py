print("Importing keyboard interface...")

from globals import INPUT

class KeyboardInterface:
    def __init__(self, inputInterface = None):
        self.setInputInterface(inputInterface)
    
    def getInputInterface(self):
        return self.__inputInterface
    
    def setInputInterface(self, inputInterface):
        self.__inputInterface = inputInterface
    
    def receive(self, key, released_prefix = None):
        
        keyStr = None
        for key_lookup in INPUT.LOOKUP:
            if key == INPUT.LOOKUP[key_lookup]:
                keyStr = key_lookup
        
        if keyStr is not None:
            if released_prefix is not None:
                keyStr = released_prefix + keyStr
            
            print(f"Recieved keyboard signal {keyStr}")
            if self.getInputInterface() is not None:
                self.getInputInterface().receive(keyStr)
            else:
                print("Keyboard has no input interface!")

keyboardInterface = KeyboardInterface()