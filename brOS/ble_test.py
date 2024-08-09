import struct
from bluepy.btle import Peripheral

remote_mac = "28:cd:c1:0d:f6:62"

def _decode_button(data):
    return struct.unpack("<h", data)[0]

print(f"Searching for device with MAC address '{remote_mac}'...")

remote = Peripheral(remote_mac)
#service = remote.getServiceByUUID("0x1849")
charcteristic = remote.getCharacteristics(uuid="00002ba5-0000-1000-8000-00805f9b34fb")
#descriptors = remote.getDescriptors()

#print(service)
#print(charcteristic)
#print(descriptors)

print("Connected\n")

read_backup = 0
while True:
    remote.waitForNotifications(0.1)
    read = charcteristic.read()
    if read != read_backup:
        print(_decode_button(read))
        read_backup = read