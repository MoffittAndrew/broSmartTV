import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
INPUT_PIN = 14

# Infrared reciever
GPIO.setup(INPUT_PIN, GPIO.IN)

IR_on = False
while True:
    if not GPIO.input(INPUT_PIN) and not IR_on:
        print("IR detected!")
        IR_on = True
        sleep(1)
    elif IR_on:
        print()
        IR_on = False