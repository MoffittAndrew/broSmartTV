print("Importing remote interface...")

from globals import REMOTE

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
        checkConnectedInterval = REMOTE.CHECK_CONNECTED_INTERVAL,
        scanTimeout = REMOTE.SCAN_TIMEOUT,
        callbackOnConnect = None,
        inputInterface = None,
        running = False,
    ):
        this.__name = name
        this.__serviceUUID = serviceUUID
        this.__characteristicUUID = characteristicUUID
        this.__checkAliveInterval = checkAliveInterval
        this.__checkConnectedInterval = checkConnectedInterval
        this.__scanTimeout = scanTimeout
        this.setCallbackOnConnect(callbackOnConnect)
        this.setInputInterface(inputInterface)
        this.setRunning(running)
        this.setConnected(False)
    
    def getName(this):
        return this.__name
    
    def getServiceUUID(this):
        return this.__serviceUUID
    
    def getCharacteristicUUID(this):
        return this.__characteristicUUID
    
    def getCheckAliveInterval(this):
        return this.__checkAliveInterval

    def getCheckConnectedInterval(this):
        return this.__checkConnectedInterval
    
    def getScanTimeout(this):
        return this.__scanTimeout
    
    def getInputInterface(this):
        return this.__inputInterface
    
    def getCallbackOnConnect(this):
        return this.__callbackOnConnect
    
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
    
    def __callback(this, sender: bleak.BleakGATTCharacteristic, data: bytearray):
        data = None if not data else data.decode()
        print(f"Recieved remote signal {data}")
        if this.getInputInterface() is not None:
            asyncio.create_task(this.getInputInterface().receive(data))
        else:
            print("Cannot handle incoming remote input, remote has no input interface!")
    
    def __disconnected_callback(this, client: bleak.BleakClient):
        print("Disconnected from remote.")
        this.setConnected(False)

    async def __connect(this):
        print("Scanning for remote...")
        device = await bleak.BleakScanner.find_device_by_name(this.getName(), timeout=this.getScanTimeout())
        if not device:
            print("Remote not found")
            return
        else:
            print("Connecting to remote...")

        async with bleak.BleakClient(device, disconnected_callback=this.__disconnected_callback) as client:
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
    
    async def init(this, callbackOnConnect = None):
        
        print("Initializing remote scan...")
        this.setRunning(True)
        this.setConnected(False)
        
        if callbackOnConnect is not None:
            this.setCallbackOnConnect(callbackOnConnect)
        
        while this.isRunning():
            try:
                await this.__connect()
            except Exception as e:
                print(f"An error occurred: {e}")
                await asyncio.sleep(this.getCheckAliveInterval())
    
    async def await_power_on(this):
        
        asyncio.create_task(this.init())
        await asyncio.sleep(this.getCheckAliveInterval())
        while this.isRunning() and not this.isConnected():
            await asyncio.sleep(this.getCheckConnectedInterval())

remoteInterface = RemoteInterface()