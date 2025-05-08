import RPi.GPIO as GPIO
import threading
import time

class LEDManager:
    def __init__(self):
        self.led_pins = {
            "TX": 5,         # GPIO 5  - pin físico 29 - LED de transmisión
            "VOLTAGE": 27,   # GPIO 27 - pin físico 13 - LED de batería
            "NET": 22,       # GPIO 22 - pin físico 15 - LED de red
            "MEDIA": 23,     # GPIO 23 - pin físico 16 - LED de almacenamiento
            "GPS": 24,       # GPIO 24 - pin físico 18 - LED de GPS (si se implementa)
            "ERROR": 25,     # GPIO 25 - pin físico 22 - LED de error
            "HB": 18         # GPIO 18 - pin físico 12 - LED heartbeat
        }

        # Control de parpadeo de batería
        self.battery_blink_active = False
        self.battery_thread = None

        GPIO.setmode(GPIO.BCM)
        for pin in self.led_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def set(self, name, state):
        pin = self.led_pins.get(name)
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
        else:
            print(f"[WARN] LED '{name}' no está definido.")

    def blink(self, name, duration=0.2):
        pin = self.led_pins.get(name)
        if pin is not None:
            threading.Thread(target=self._blink_worker, args=(pin, duration), daemon=True).start()

    def _blink_worker(self, pin, duration):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(pin, GPIO.LOW)

    def heartbeat(self, on_time=0.2, off_time=0.8):
        def pulse():
            pin = self.led_pins.get("HB")
            while True:
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(on_time)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(off_time)
        threading.Thread(target=pulse, daemon=True).start()

    def set_battery_status(self, status):
        """
        Controla el LED de batería (VOLTAGE):
        - NORMAL: Apagado
        - BAJA: Parpadeo lento
        - CRÍTICA: Parpadeo rápido
        """
        pin = self.led_pins.get("VOLTAGE")
        if pin is None:
            print("[WARN] LED de batería (VOLTAGE) no configurado.")
            return

        if status == "NORMAL":
            self._stop_blinker()
            GPIO.output(pin, GPIO.LOW)
            self.set("ERROR", False)  # 🔴 Apaga el LED de error

        elif status == "BAJA":
            self._start_blinker(pin, on_time=1.5, off_time=1.0)
            self.set("ERROR", False)  # 🔴 Apaga el LED de error

        elif status == "CRÍTICA":
            self._start_blinker(pin, on_time=0.1, off_time=0.1)
            self.set("ERROR", True)   # 🔴 Enciende el LED de error

    def _start_blinker(self, pin, on_time, off_time):
        """Inicia parpadeo controlado para el LED de batería."""
        if self.battery_blink_active:
            return  # Ya está activo
        self.battery_blink_active = True

        def blink_loop():
            while self.battery_blink_active:
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(on_time)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(off_time)

        self.battery_thread = threading.Thread(target=blink_loop, daemon=True)
        self.battery_thread.start()

    def _stop_blinker(self):
        """Detiene el parpadeo del LED de batería."""
        self.battery_blink_active = False
        if self.battery_thread:
            self.battery_thread.join(timeout=0.1)
        self.battery_thread = None