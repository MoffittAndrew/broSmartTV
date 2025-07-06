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

class Remote:
    def __init__(
        this,
        name = REMOTE.NAME,
        serviceUUID = REMOTE.SERVICE_UUID,
        characteristicUUID = REMOTE.CHARACTERISTIC_UUID,
        checkAliveInterval = REMOTE.CHECK_ALIVE_INTERVAL,
        scanTimeout = REMOTE.SCAN_TIMEOUT,
        inputInterface = None,
        running = False,
    ):
        this.__name = name
        this.__serviceUUID = serviceUUID
        this.__characteristicUUID = characteristicUUID
        this.__checkAliveInterval = checkAliveInterval
        this.__scanTimeout = scanTimeout
        this.__inputInterface = inputInterface
        this.__running = running
    
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
    
    def isRunning(this):
        return this.__running
    
    def setInputInterface(this, inputInterface):
        this.__inputInterface = inputInterface
        
    def setRunning(this, running):
        this.__running = running
    
    def __callback(this, sender: bleak.BleakGATTCharacteristic, data: bytearray):
        data = None if not data else data.decode()
        print(f"Recieved remote signal {data}")
        if this.getInputInterface() is not None:
            this.getInputInterface().receive(data)
        else:
            print("Remote has no input interface!")
        
    def __disconnected_callback(this, client: bleak.BleakClient):
        print("Disconnected from remote.")

    async def __connect(this):
        print("Scanning for remote...")
        device = await bleak.BleakScanner.find_device_by_name(this.getName(), timeout=this.getScanTimeout())
        if not device:
            print("Remote not found")
            return
        else:
            print("Connecting...")

        async with bleak.BleakClient(device, disconnected_callback=this.__disconnected_callback) as client:
            service = client.services.get_service(this.getServiceUUID())
            if service is None:
                print("Service not found")
                return

            characteristic = service.get_characteristic(this.getCharacteristicUUID())
            if characteristic is None:
                print("Characteristic not found")
                return

            print("Connected")
            await client.start_notify(characteristic, this.__callback)
            while client.is_connected:
                await asyncio.sleep(this.getCheckAliveInterval())
        
    async def init(this):
        
        print("Initializing remote loop")
        this.setRunning(True)
        if this.getInputInterface() is not None:
            while this.isRunning():
                try:
                    await remote.__connect()
                except Exception as e:
                    print(f"An error occurred: {e}")
                    await asyncio.sleep(this.getCheckAliveInterval())
        else:
            print("Unable to initialize remote object, no input interface is set!")
        
        print("Shutting down remote loop...")

remote = Remote()