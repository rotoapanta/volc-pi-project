import RPi.GPIO as GPIO
import time

class RainSensor:
    def __init__(self, pin, bounce_time, callback):
        self.pin = pin
        self.bounce_time = bounce_time
        self.callback = callback
        self.last_impulse_time = time.time()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self._debounced_callback, bouncetime=self.bounce_time)

    def _debounced_callback(self, channel):
        current_time = time.time()
        if (current_time - self.last_impulse_time) > (self.bounce_time / 1000):
            self.callback()
            self.last_impulse_time = current_time
