import struct
from bluepy.btle import Peripheral

remote_mac = "28:cd:c1:0d:f6:62"

def _decode_button(data):
    return struct.unpack("<h", data)[0] / 100

print(f"Searching for device with MAC address '{remote_mac}'...")

remote = Peripheral(remote_mac)
#service = remote.getServiceByUUID("0x1849")
charcteristic = remote.getCharacteristics()[-1]
#descriptors = remote.getDescriptors()

#print(service)
#print(charcteristic)
#print(descriptors)

print("Connected")

while True:
    remote.waitForNotifications(1)
    read = charcteristic.read()
    print()
    print(charcteristic.uuid)
    print(read)
    print(_decode_button(read))