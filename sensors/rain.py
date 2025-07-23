# sensors/rain.py
import lgpio
import threading
import time

class RainSensor:
    def __init__(self, pin, debounce_ms, callback, poll_interval=0.002):
        self.pin = pin
        self.debounce_ms = debounce_ms
        self.callback = callback
        self.poll_interval = poll_interval  # segundos
        self.chip = lgpio.gpiochip_open(0)
        self._stop_event = threading.Event()
        self._thread = None
        self._last_state = 1  # Asumimos pull-up
        self._last_time = 0

    def setup(self):
        try:
            lgpio.gpio_claim_input(self.chip, self.pin)
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
        except Exception as e:
            raise RuntimeError(f"Error configurando sensor de lluvia: {e}")

    def _poll_loop(self):
        while not self._stop_event.is_set():
            state = lgpio.gpio_read(self.chip, self.pin)
            now = time.time()
            # Detecta flanco descendente con antirrebote
            if self._last_state == 1 and state == 0:
                if (now - self._last_time) * 1000 > self.debounce_ms:
                    self._last_time = now
                    self.callback()
            self._last_state = state
            time.sleep(self.poll_interval)

    def cleanup(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.1)
        try:
            lgpio.gpiochip_close(self.chip)
        except Exception as e:
            print(f"[WARN] Error al limpiar sensor de lluvia: {e}")
