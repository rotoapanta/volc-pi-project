# utils/leds_utils.py

import lgpio
import threading
import time

class LEDManager:
    def __init__(self):
        self.led_pins = {
            "HB": 5,
            "VOLTAGE": 6,
            "ETH": 16,
            "TX": 22,
            "GPS": 24,
            "MEDIA": 25,
            "ERROR": 26,
            "WIFI": 27  # Nuevo LED para WiFi en GPIO27 (pin físico 13)
        }
        self.chip = lgpio.gpiochip_open(0)
        self.blink_active = {}
        self.blink_threads = {}
        for pin in self.led_pins.values():
            try:
                lgpio.gpio_claim_output(self.chip, pin)
                lgpio.gpio_write(self.chip, pin, 0)
            except Exception as e:
                print(f"[WARN] No se pudo configurar GPIO {pin}: {e}")

    def set(self, name, state):
        pin = self.led_pins.get(name)
        if pin is not None:
            self._stop_blinker(pin)
            try:
                lgpio.gpio_write(self.chip, pin, 1 if state else 0)
            except Exception as e:
                print(f"[WARN] No se pudo escribir en GPIO {pin}: {e}")
        else:
            print(f"[WARN] LED '{name}' no está definido.")

    def blink(self, name, duration=0.2):
        pin = self.led_pins.get(name)
        if pin:
            threading.Thread(target=self._blink_once, args=(pin, duration), daemon=True).start()

    def _blink_once(self, pin, duration):
        try:
            lgpio.gpio_write(self.chip, pin, 1)
            time.sleep(duration)
            lgpio.gpio_write(self.chip, pin, 0)
        except Exception as e:
            print(f"[WARN] Error al parpadear GPIO {pin}: {e}")

    def heartbeat(self, on_time=0.2, off_time=0.8):
        def pulse():
            pin = self.led_pins.get("HB")
            while True:
                try:
                    lgpio.gpio_write(self.chip, pin, 1)
                    time.sleep(on_time)
                    lgpio.gpio_write(self.chip, pin, 0)
                    time.sleep(off_time)
                except Exception as e:
                    print(f"[WARN] Error en heartbeat GPIO {pin}: {e}")
                    break
        threading.Thread(target=pulse, daemon=True).start()

    def _start_blinker(self, pin, on_time, off_time):
        self._stop_blinker(pin)
        self.blink_active[pin] = True
        def blink_loop():
            while self.blink_active.get(pin, False):
                try:
                    lgpio.gpio_write(self.chip, pin, 1)
                    time.sleep(on_time)
                    lgpio.gpio_write(self.chip, pin, 0)
                    time.sleep(off_time)
                except Exception as e:
                    print(f"[WARN] Error en blinker GPIO {pin}: {e}")
                    break
        thread = threading.Thread(target=blink_loop, daemon=True)
        self.blink_threads[pin] = thread
        thread.start()

    def _stop_blinker(self, pin):
        self.blink_active[pin] = False
        thread = self.blink_threads.get(pin)
        if thread:
            thread.join(timeout=0.1)
            del self.blink_threads[pin]

    def set_battery_status(self, status):
        pin = self.led_pins.get("VOLTAGE")
        if pin is None:
            print("[WARN] LED de batería no configurado.")
            return
        if status == "NORMAL":
            self._stop_blinker(pin)
            try:
                lgpio.gpio_write(self.chip, pin, 0)
                self.set("ERROR", False)
            except Exception as e:
                print(f"[WARN] No se pudo escribir en GPIO {pin}: {e}")
        elif status == "BAJA":
            self._start_blinker(pin, on_time=1.5, off_time=1.5)
            self.set("ERROR", False)
        elif status == "CRÍTICA":
            self._start_blinker(pin, on_time=0.2, off_time=0.2)
            self.set("ERROR", True)

    def set_gps_status(self, status):
        pin = self.led_pins.get("GPS")
        if pin is None:
            print("[WARN] LED de GPS no configurado.")
            return
        if status == "NO_FIX":
            self._stop_blinker(pin)
            try:
                lgpio.gpio_write(self.chip, pin, 0)
            except Exception as e:
                print(f"[WARN] No se pudo escribir en GPIO {pin}: {e}")
        elif status == "FIX":
            self._stop_blinker(pin)
            try:
                lgpio.gpio_write(self.chip, pin, 1)
            except Exception as e:
                print(f"[WARN] No se pudo escribir en GPIO {pin}: {e}")
        elif status == "SEARCHING":
            self._start_blinker(pin, on_time=1.0, off_time=1.0)

    def set_network_status(self, eth_ip, wlan_ip):
        """Controla los LEDs de red según el estado de las interfaces."""
        # LED Ethernet
        pin_eth = self.led_pins.get("ETH")
        if pin_eth is not None:
            self._stop_blinker(pin_eth)
            try:
                lgpio.gpio_write(self.chip, pin_eth, 1 if eth_ip else 0)
            except Exception as e:
                print(f"[WARN] No se pudo escribir en GPIO {pin_eth}: {e}")
        else:
            print("[WARN] LED 'ETH' no está definido.")
        # LED WiFi
        pin_wifi = self.led_pins.get("WIFI")
        if pin_wifi is not None:
            self._stop_blinker(pin_wifi)
            try:
                lgpio.gpio_write(self.chip, pin_wifi, 1 if wlan_ip else 0)
            except Exception as e:
                print(f"[WARN] No se pudo escribir en GPIO {pin_wifi}: {e}")
        else:
            print("[WARN] LED 'WIFI' no está definido.")

    def cleanup(self):
        for pin in self.led_pins.values():
            try:
                lgpio.gpio_write(self.chip, pin, 0)
            except Exception as e:
                print(f"[WARN] No se pudo limpiar GPIO {pin}: {e}")
        lgpio.gpiochip_close(self.chip)
