import asyncio

import bleak

_REMOTE_NAME = "bro-ito"
# org.bluetooth.service.media_control
_SERVICE_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x1849)
# org.bluetooth.characteristic.media_control_point
_CHARACTERISTIC_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2BA5)



def _callback(sender: bleak.BleakGATTCharacteristic, data: bytearray):
    data = None if not data else data.decode()
    print(f"Recieved signal {data}")


async def find_temp_sensor():
    name = _REMOTE_NAME
    return await bleak.BleakScanner.find_device_by_name(name)


async def do_connect():
    print("Scanning for remote...")
    device = await find_temp_sensor()
    if not device:
        print("Remote not found")
        return
    else:
        print("Connected")

    async with bleak.BleakClient(device) as client:
        service = client.services.get_service(_SERVICE_UUID)
        if service is None:
            print("Service not found")
            return

        characteristic = service.get_characteristic(_CHARACTERISTIC_UUID)
        if characteristic is None:
            print("Characteristic not found")
            return

        await client.start_notify(characteristic, _callback)
        while client.is_connected:
            await asyncio.sleep(1)
    
    print("Disconnected.")


async def main():
    while True:
        await do_connect()

asyncio.run(main())