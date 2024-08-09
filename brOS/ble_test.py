import struct
from bluepy.btle import Peripheral

remote_mac = "28:cd:c1:0d:f6:61"

print(f"Searching for device with MAC address '{remote_mac}'")

remote = Peripheral(remote_mac)
service = remote.getServiceByUUID("0x1849")
charcteristics = remote.getCharacteristics()
descriptors = remote.getDescriptors()

print(service)
print(charcteristics)
print(descriptors)

def _decode_button(data):
    return struct.unpack("<h", data)[0] / 100

while True:
    remote.waitForNotifications()
    read = remote.readCharacteristic(charcteristics[0])
    print(read)
    print(_decode_button(read))