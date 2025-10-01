# utils/leds_utils.py

import lgpio
import threading
import time
import atexit
from utils.log_utils import setup_logger
logger = setup_logger("leds", log_file="leds.log")

class LEDManager:
    def __init__(self):
        self.led_pins = {
            "HB": 5,
            "VOLTAGE": 6,
            "ETH": 16,
            "TX": 27,   # LORA ESTE led es aumentado
            "GPS": 24,
            "MEDIA": 25,    
            "ERROR": 26,    #
            "WIFI": 22  # Nuevo LED para WiFi en GPIO27 (pin físico 13)
        }
        self.chip = lgpio.gpiochip_open(0)
        self.blink_active = {}
        self.blink_threads = {}
        self.heartbeat_active = True
        self.heartbeat_thread = None
        self._cleaned = False
        for pin in self.led_pins.values():
            try:
                try:
                    lgpio.gpio_free(self.chip, pin)  # Intenta liberar el pin si está ocupado
                except Exception:
                    pass  # Si no estaba ocupado, ignora el error
                lgpio.gpio_claim_output(self.chip, pin)
                lgpio.gpio_write(self.chip, pin, 0)
            except Exception as e:
                logger.warning(f"No se pudo configurar GPIO {pin}: {e}")
        # Registrar cleanup automático al salir
        atexit.register(self.cleanup)

    def set(self, name, state):
        pin = self.led_pins.get(name)
        if pin is not None:
            self._stop_blinker(pin)
            try:
                lgpio.gpio_write(self.chip, pin, 1 if state else 0)
            except Exception as e:
                logger.warning(f"No se pudo escribir en GPIO {pin}: {e}")
        else:
            logger.warning(f"LED '{name}' no está definido.")

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
            logger.warning(f"Error al parpadear GPIO {pin}: {e}")

    def heartbeat(self, on_time=0.2, off_time=0.8):
        def pulse():
            pin = self.led_pins.get("HB")
            logger.info("Heartbeat thread started")
            while self.heartbeat_active:
                try:
                    lgpio.gpio_write(self.chip, pin, 1)
                    time.sleep(on_time)
                    lgpio.gpio_write(self.chip, pin, 0)
                    time.sleep(off_time)
                except Exception as e:
                    logger.warning(f"Error en heartbeat GPIO {pin}: {e}")
                    break
        self.heartbeat_active = True
        self.heartbeat_thread = threading.Thread(target=pulse, daemon=True)
        self.heartbeat_thread.start()

    def stop_heartbeat(self):
        self.heartbeat_active = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=0.5)
            self.heartbeat_thread = None

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
                    logger.warning(f"Error en blinker GPIO {pin}: {e}")
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
            logger.warning("LED de batería no configurado.")
            return
        if status == "NORMAL":
            self._stop_blinker(pin)
            try:
                lgpio.gpio_write(self.chip, pin, 0)
                self.set("ERROR", False)
            except Exception as e:
                logger.warning(f"No se pudo escribir en GPIO {pin}: {e}")
        elif status == "BAJA":
            self._start_blinker(pin, on_time=1.5, off_time=1.5)
            self.set("ERROR", False)
        elif status == "CRÍTICA":
            self._start_blinker(pin, on_time=0.2, off_time=0.2)
            self.set("ERROR", True)

    def set_gps_status(self, status):
        pin = self.led_pins.get("GPS")
        if pin is None:
            logger.warning("LED de GPS no configurado.")
            return
        if status == "NO_FIX":
            self._stop_blinker(pin)
            try:
                lgpio.gpio_write(self.chip, pin, 0)
            except Exception as e:
                logger.warning(f"No se pudo escribir en GPIO {pin}: {e}")
        elif status == "FIX":
            self._stop_blinker(pin)
            try:
                lgpio.gpio_write(self.chip, pin, 1)
            except Exception as e:
                logger.warning(f"No se pudo escribir en GPIO {pin}: {e}")
        elif status == "SEARCHING":
            self._start_blinker(pin, on_time=1.0, off_time=1.0)

    def set_network_status(self, eth_ip, wlan_ip):
        """Controla los LEDs de red según el estado de las interfaces, evitando reinicios innecesarios del parpadeo."""
        # LED Ethernet
        pin_eth = self.led_pins.get("ETH")
        eth_connected = bool(eth_ip)
        if pin_eth is not None:
            if eth_connected != getattr(self, 'last_eth_connected', None):
                self._stop_blinker(pin_eth)
                if eth_connected:
                    self._start_blinker(pin_eth, on_time=0.8, off_time=0.8)
                else:
                    try:
                        lgpio.gpio_write(self.chip, pin_eth, 0)
                    except Exception as e:
                        logger.warning(f"No se pudo escribir en GPIO {pin_eth}: {e}")
                self.last_eth_connected = eth_connected
        else:
            logger.warning("LED 'ETH' no está definido.")
        # LED WiFi
        pin_wifi = self.led_pins.get("WIFI")
        wifi_connected = bool(wlan_ip)
        if pin_wifi is not None:
            if wifi_connected != getattr(self, 'last_wifi_connected', None):
                self._stop_blinker(pin_wifi)
                if wifi_connected:
                    self._start_blinker(pin_wifi, on_time=0.8, off_time=0.8)
                else:
                    try:
                        lgpio.gpio_write(self.chip, pin_wifi, 0)
                    except Exception as e:
                        logger.warning(f"No se pudo escribir en GPIO {pin_wifi}: {e}")
                self.last_wifi_connected = wifi_connected
        else:
            logger.warning("LED 'WIFI' no está definido.")

    def cleanup(self):
        # Evitar limpieza doble o uso de handle cerrado
        if getattr(self, "_cleaned", False) or getattr(self, "chip", None) is None:
            return
        self._cleaned = True

        # Detener hilos de latido y blinker antes de liberar GPIO
        self.stop_heartbeat()
        try:
            for pin in list(self.blink_threads.keys()):
                self._stop_blinker(pin)
        except Exception:
            pass

        # Apagar LEDs y liberar líneas
        for pin in self.led_pins.values():
            try:
                lgpio.gpio_write(self.chip, pin, 0)
            except Exception:
                # Evitar warnings ruidosos durante apagado si el handle ya no es válido
                pass
            try:
                lgpio.gpio_free(self.chip, pin)
            except Exception:
                pass
        # Cerrar el chip y anular referencia
        try:
            lgpio.gpiochip_close(self.chip)
        except Exception:
            pass
        self.chip = None
