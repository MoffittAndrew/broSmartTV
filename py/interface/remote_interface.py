print("Importing remote interface...")

from globals import REMOTE, INPUT

import asyncio
import bleak

try:
    from bleak.backends.winrt.util import allow_sta
    # tell Bleak we are using a graphical user interface that has been properly
    # configured to work with asyncio
    allow_sta()
except ImportError:
    # other OSes and older versions of Bleak will raise ImportError which we
    # can safely ignore
    pass

class RemoteInterface:
    def __init__(
        this,
        name = REMOTE.NAME,
        serviceUUID = REMOTE.SERVICE_UUID,
        characteristicUUID = REMOTE.CHARACTERISTIC_UUID,
        checkAliveInterval = REMOTE.CHECK_ALIVE_INTERVAL,
        scanTimeout = REMOTE.SCAN_TIMEOUT,
        callbackOnConnect = None,
        inputInterface = None,
        running = False,
    ):
        this.__name = name
        this.__serviceUUID = serviceUUID
        this.__characteristicUUID = characteristicUUID
        this.__checkAliveInterval = checkAliveInterval
        this.__scanTimeout = scanTimeout
        this.setCallbackOnConnect(callbackOnConnect)
        this.setInputInterface(inputInterface)
        this.setRunning(running)
        this.setConnected(False)
        this.setDevice(None)
        this.setClient(None)
    
    def getName(this):
        return this.__name
    
    def getServiceUUID(this):
        return this.__serviceUUID
    
    def getCharacteristicUUID(this):
        return this.__characteristicUUID
    
    def getCheckAliveInterval(this):
        return this.__checkAliveInterval
    
    def getScanTimeout(this):
        return this.__scanTimeout
    
    def getInputInterface(this):
        return this.__inputInterface
    
    def getCallbackOnConnect(this):
        return this.__callbackOnConnect
    
    def getDevice(this):
        return this.__device

    def getClient(this):
        return this.__client
    
    def isRunning(this):
        return this.__running
    
    def isConnected(this):
        return this.__connected
    
    def setCallbackOnConnect(this, callback):
        this.__callbackOnConnect = callback
    
    def setInputInterface(this, inputInterface):
        this.__inputInterface = inputInterface
    
    def setRunning(this, running):
        this.__running = running
    
    def setConnected(this, connected):
        this.__connected = connected
    
    def setDevice(this, device):
        this.__device = device
    
    def setClient(this, client):
        this.__client = client
    
    async def __findRemote(this):
        print("Scanning for remote...")
        this.setDevice(await bleak.BleakScanner.find_device_by_name(this.getName(), timeout=this.getScanTimeout()))
    
    def __callback(this, sender: bleak.BleakGATTCharacteristic, data: bytearray):
        data = None if not data else data.decode()
        print(f"Recieved remote signal {data}")
        if this.getInputInterface() is not None:
            asyncio.create_task(this.getInputInterface().receive(data))
            if data == INPUT.POWER:
                asyncio.create_task(this.disconnect())
        else:
            print("Cannot handle incoming remote input, remote has no input interface!")
    
    def __disconnected_callback(this, client: bleak.BleakClient):
        print("Disconnected from remote.")
        this.setConnected(False)

    async def __connectToRemote(this):
        async with bleak.BleakClient(this.getDevice(), disconnected_callback=this.__disconnected_callback) as client:
            this.setClient(client)
            service = client.services.get_service(this.getServiceUUID())
            if service is None:
                print("Service not found")
                return

            characteristic = service.get_characteristic(this.getCharacteristicUUID())
            if characteristic is None:
                print("Characteristic not found")
                return

            print("Remote connected")
            this.setConnected(True)
            if this.getCallbackOnConnect() is not None:
                callback = this.getCallbackOnConnect()
                this.setCallbackOnConnect(None)
                asyncio.create_task(callback())
            
            await client.start_notify(characteristic, this.__callback)
            while client.is_connected:
                await asyncio.sleep(this.getCheckAliveInterval())
    
    async def connect(this, callbackOnConnect = None):
        
        if callbackOnConnect is not None:
            this.setCallbackOnConnect(callbackOnConnect)
        
        this.setRunning(True)
        while this.isRunning():
            try:
                if not this.getDevice():
                    print("Remote not found, scanning again...")
                    await this.__findRemote()
                else:
                    print("Connecting to remote...")
                    await this.__connectToRemote()
            
            except Exception as e:
                print(f"An error occurred: {e}")
                await asyncio.sleep(this.getCheckAliveInterval())
    
    async def awaitFindRemote(this):
        
        print("Initializing remote scan...")
        this.setRunning(True)
        this.setConnected(False)
        
        waiting = True
        while waiting:
            await this.__findRemote()
            if not this.getDevice():
                print("Remote not found")
            else:
                print("Remote found!")
                waiting = False
    
    async def disconnect(this):
        print("Disconnecting from remote...")
        this.setRunning(False)
        if this.getClient() is not None:
            await this.getClient().disconnect()
        else:
            print("Cannot disconnect from remote, as there is no remote connected!")

remoteInterface = RemoteInterface()