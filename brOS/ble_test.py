import struct
from bluepy.btle import Peripheral

remote_mac = "28:cd:c1:0d:f6:62"

print(f"Searching for device with MAC address '{remote_mac}'...")

remote = Peripheral(remote_mac)
#service = remote.getServiceByUUID("0x1849")
charcteristic = remote.getCharacteristics(uuid="0x7660ca10")
descriptors = remote.getDescriptors()

#print(service)
print(charcteristic)
print(descriptors)

def _decode_button(data):
    return struct.unpack("<h", data)[0] / 100

while True:
    remote.waitForNotifications(600)
    read = remote.readCharacteristic(charcteristic)
    print(read)
    print(_decode_button(read))