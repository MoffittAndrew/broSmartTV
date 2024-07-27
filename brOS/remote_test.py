import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
INPUT_PIN = 14

# Infrared reciever
GPIO.setup(INPUT_PIN, GPIO.IN)

while True:
    print(GPIO.input(INPUT_PIN))