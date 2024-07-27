import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
INPUT_PIN = 14

# Infrared reciever
GPIO.setup(INPUT_PIN, GPIO.IN)

IR_on = False
while True:
    if not GPIO.input(INPUT_PIN) and not IR_on:
        print("IR detected!")
        IR_on = True
    elif IR_on:
            print()