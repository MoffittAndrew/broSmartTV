# The remote starts in sleep mode in order to save
# as much power as possible. When a user presses a
# button, the remote wakes up and activates BLE,
# then tries to establish a connection to the TV.
#
# This file should be as small and effecient as possible

print("Initialising...")


def init_buttons():
    from machine import Pin
    
    buttons = []
    for pin_no in range(10, 22):
        buttons.append(Pin(pin_no, Pin.IN, Pin.PULL_DOWN))
        
    return buttons


def activate_ble(buttons, i):
    from ble import main as ble_main
    
    ble_main(buttons, i)


def main():
    buttons = init_buttons()
    while True:
        for i in range(len(buttons)):
            if buttons[i].value():
                activate_ble(buttons, i)


print("Ready!")
main()
