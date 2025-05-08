import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.OUT)

print("Encendiendo LED GPIO27(pin físico 15)...")
GPIO.output(22, GPIO.HIGH)
time.sleep(3)
print("Apagando...")
GPIO.output(22, GPIO.LOW)
GPIO.cleanup()
