from bluepy import Peripheral

remote_mac = "28:cd:c1:0d:f6:61"

remote = Peripheral(remote_mac)
service = remote.getServiceByUUID("0x1849")
charcteristics = remote.getCharacteristics()
descriptors = remote.getDescriptors()

print(service)
print(charcteristics)
print(descriptors)

while True:
    remote.waitForNotifications()
    print(remote.readCharacteristic(charcteristics[0]))