from globals import REMOTE

import asyncio
import bleak

class Remote:
    def __init__(
        this,
        name = REMOTE.NAME,
        serviceUUID = REMOTE.SERVICE_UUID,
        characteristicUUID = REMOTE.CHARACTERISTIC_UUID,
        checkAliveInterval = REMOTE.CHECK_ALIVE_INTERVAL,
        inputInterface = None,
    ):
        this.__name = name
        this.__serviceUUID = serviceUUID
        this.__characteristicUUID = characteristicUUID
        this.__checkAliveInterval = checkAliveInterval
        this.__inputInterface = inputInterface
    
    def getName(this):
        return this.__name
    
    def getServiceUUID(this):
        return this.__serviceUUID
    
    def getCharacteristicUUID(this):
        return this.__characteristicUUID
    
    def getCheckAliveInterval(this):
        return this.__checkAliveInterval
    
    def getInputInterface(this):
        return this.__inputInterface
    
    def setInputInterface(this, inputInterface):
        this.__inputInterface = inputInterface
    
    def __callback(this, sender: bleak.BleakGATTCharacteristic, data: bytearray):
        data = None if not data else data.decode()
        print(f"Recieved signal {data}")
        this.getInputInterface().receive(data)
        
    def __disconnected_callback(this, client: bleak.BleakClient):
        print("Disconnected from remote.")

    async def __connect(this):
        print("Scanning for remote...")
        device = await bleak.BleakScanner.find_device_by_name(this.getName(), timeout=None)
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
        
    async def __main(this):
        while True:
            try:
                await remote.__connect()
            except Exception as e:
                print(f"An error occurred: {e}")

    def init(this):
        if this.getInputInterface() != None:
            asyncio.run(this.__main())
        else:
            print("Unable to initialize remote object, no input interface is set!")

remote = Remote()