print("Importing remote interface...")

from globals import REMOTE, INPUT

import asyncio
import sys
import bleak
import traceback

if sys.platform.startswith("win"):
    try:
        from bleak.backends.winrt.util import allow_sta
        # tell Bleak we are using a graphical user interface that has been
        # properly configured to work with asyncio
        allow_sta()
    except (ImportError, AttributeError):
        # Older Bleak versions or partial WinRT environments can fail here;
        # we can safely continue without this optimization.
        pass

class RemoteInterface:
    def __init__(
        self,
        name = REMOTE.NAME,
        serviceUUID = REMOTE.SERVICE_UUID,
        characteristicUUID = REMOTE.CHARACTERISTIC_UUID,
        checkAliveInterval = REMOTE.CHECK_ALIVE_INTERVAL,
        scanTimeout = REMOTE.SCAN_TIMEOUT,
        callbackOnConnect = None,
        inputInterface = None,
        running = False,
    ):
        self.__name = name
        self.__serviceUUID = serviceUUID
        self.__characteristicUUID = characteristicUUID
        self.__checkAliveInterval = checkAliveInterval
        self.__scanTimeout = scanTimeout
        self.setCallbackOnConnect(callbackOnConnect)
        self.setInputInterface(inputInterface)
        self.setRunning(running)
        self.setConnected(False)
        self.setDevice(None)
        self.setClient(None)
        self.__connecting = False
        self.__interrupted_notice_printed = False
    
    def getName(self):
        return self.__name
    
    def getServiceUUID(self):
        return self.__serviceUUID
    
    def getCharacteristicUUID(self):
        return self.__characteristicUUID
    
    def getCheckAliveInterval(self):
        return self.__checkAliveInterval
    
    def getScanTimeout(self):
        return self.__scanTimeout
    
    def getInputInterface(self):
        return self.__inputInterface
    
    def getCallbackOnConnect(self):
        return self.__callbackOnConnect
    
    def getDevice(self):
        return self.__device

    def getClient(self):
        return self.__client
    
    def isRunning(self):
        return self.__running
    
    def isConnected(self):
        return self.__connected
    
    def setCallbackOnConnect(self, callback):
        self.__callbackOnConnect = callback
    
    def setInputInterface(self, inputInterface):
        self.__inputInterface = inputInterface
    
    def setRunning(self, running):
        self.__running = running
    
    def setConnected(self, connected):
        self.__connected = connected
    
    def setDevice(self, device):
        self.__device = device
    
    def setClient(self, client):
        self.__client = client
    
    async def __findRemote(self):
        print("Scanning for remote...")
        self.setDevice(await bleak.BleakScanner.find_device_by_name(self.getName(), timeout=self.getScanTimeout()))
    
    def __callback(self, sender: bleak.BleakGATTCharacteristic, data: bytearray):
        data = None if not data else data.decode()
        print(f"Recieved remote signal {data}")
        if self.getInputInterface() is not None:
            self.getInputInterface().receive(data)
            if data == INPUT.RELEASED_PREFIX + INPUT.POWER:
                asyncio.create_task(self.disconnect())
        else:
            print("Cannot handle incoming remote input, remote has no input interface!")
    
    def __disconnected_callback(self, client: bleak.BleakClient):
        if self.isConnected():
            print("Disconnected from remote.")
            self.setDevice(None)
        elif self.__connecting:
            if not self.__interrupted_notice_printed:
                print("Connection attempt to remote was interrupted.")
                self.__interrupted_notice_printed = True
        else:
            print("Connection to remote failed.")
        self.setConnected(False)
        self.setClient(None)

    async def __refresh_device_for_connect(self, device):
        """Refresh BlueZ device object by address to avoid stale scan handles."""
        address = device.address if hasattr(device, "address") else None
        if not address:
            return device

        refreshed = await bleak.BleakScanner.find_device_by_address(address, timeout=3)
        if refreshed is not None:
            self.setDevice(refreshed)
            return refreshed

        print(f"Could not refresh device by address {address}, using cached scan result.")
        return device

    async def __connectToRemote(self):
        device = self.getDevice()
        device = await self.__refresh_device_for_connect(device)
        target = device.address if hasattr(device, "address") else device
        self.__connecting = True
        self.__interrupted_notice_printed = False
        try:
            # BlueZ can keep stale device paths from scan results; connecting by
            # address is generally more reliable than passing a BLEDevice object.
            async with bleak.BleakClient(
                target,
                disconnected_callback=self.__disconnected_callback,
                timeout=max(15, self.getCheckAliveInterval() * 3),
            ) as client:
                self.setClient(client)
                service = client.services.get_service(self.getServiceUUID())
                if service is None:
                    print("Service not found")
                    return

                characteristic = service.get_characteristic(self.getCharacteristicUUID())
                if characteristic is None:
                    print("Characteristic not found")
                    return

                print("Remote connected")
                self.setConnected(True)
                if self.getCallbackOnConnect() is not None:
                    callback = self.getCallbackOnConnect()
                    self.setCallbackOnConnect(None)
                    asyncio.create_task(callback())
                
                await client.start_notify(characteristic, self.__callback)
                while client.is_connected:
                    await asyncio.sleep(self.getCheckAliveInterval())
        except Exception:
            print("Remote connection attempt failed in __connectToRemote")
            print(f"Device context: {device!r}")
            print(f"Connection target: {target!r}")
            traceback.print_exc()
            raise
        finally:
            self.__connecting = False
    
    async def connect(self, callbackOnConnect = None):
        
        if callbackOnConnect is not None:
            self.setCallbackOnConnect(callbackOnConnect)
        
        self.setRunning(True)
        while self.isRunning():
            try:
                if self.getDevice() is None:
                    print("Remote not found, scanning again...")
                    await self.__findRemote()
                else:
                    print("Connecting to remote...")
                    await self.__connectToRemote()
            
            except Exception as e:
                print("An error occurred while managing remote connection loop:")
                print(f"Exception type: {type(e).__name__}")
                print(f"Exception repr: {e!r}")
                traceback.print_exc()
                self.setDevice(None)
                await asyncio.sleep(self.getCheckAliveInterval())
    
    async def awaitFindRemote(self):
        
        print("Initializing remote scan...")
        self.setRunning(True)
        self.setConnected(False)
        
        waiting = True
        while waiting:
            await self.__findRemote()
            if not self.getDevice():
                print("Remote not found")
            else:
                print("Remote found!")
                waiting = False
    
    async def disconnect(self):
        print("Disconnecting from remote...")
        self.setRunning(False)
        if self.getClient() is not None:
            await self.getClient().disconnect()
        else:
            print("Cannot disconnect from remote, as there is no remote connected!")

remoteInterface = RemoteInterface()