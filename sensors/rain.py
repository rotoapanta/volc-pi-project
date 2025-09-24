from .base_sensor import BaseSensor
import time
import threading
import lgpio
from config import RAIN_SENSOR_PIN, BOUNCE_TIME

class RainSensor(BaseSensor):
    def __init__(self, config, logger=None):
        super().__init__(config, logger)
        self.tips = 0
        self.accumulated = 0.0  # mm
        self._lock = threading.Lock()
        self._stop = False
        # Configuración de GPIO con lgpio y arranque del monitor con antirrebote
        try:
            self.chip = lgpio.gpiochip_open(0)
            lgpio.gpio_claim_input(self.chip, RAIN_SENSOR_PIN)
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            if self.logger:
                self.logger.info(f"RainSensor iniciado | GPIO={RAIN_SENSOR_PIN} | BOUNCE={BOUNCE_TIME} ms")
        except Exception as e:
            self.chip = None
            self._monitor_thread = None
            if self.logger:
                self.logger.error(f"Error inicializando RainSensor (GPIO): {e}")

    def tip_callback(self, channel=None):
        with self._lock:
            self.tips += 1
            self.accumulated += 0.25  # mm por basculamiento
            tips = self.tips
            accumulated = self.accumulated
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[PLUVIOMETER] TIME={timestamp} TIPS={tips:02d} ACCUMULATED_RAIN={accumulated:.2f}mm"
        if self.logger:
            self.logger.info(msg)

    def acquire(self):
        # Retorna el acumulado desde el último reinicio (mm)
        with self._lock:
            return self.accumulated

    def process(self, raw_data):
        # raw_data debe ser un dict con al menos NIVEL, LATITUD, LONGITUD, ALTURA, BATERIA
        data = {
            "FECHA": time.strftime("%Y-%m-%d"),
            "TIEMPO": time.strftime("%H:%M:%S"),
            "NIVEL": raw_data.get("NIVEL", 0.0),
            "LATITUD": raw_data.get("LATITUD"),
            "LONGITUD": raw_data.get("LONGITUD"),
            "ALTURA": raw_data.get("ALTURA"),
            "BATERIA": raw_data.get("BATERIA")
        }
        self.tips = 0
        self.accumulated = 0.0
        return data

    def _monitor_loop(self):
        """
        Monitor por sondeo del pin de pluviómetro con antirrebote por tiempo.
        Detecta flanco de caída (1->0) y llama tip_callback.
        """
        # Estado inicial del pin (asumimos pull-up con contacto a GND)
        try:
            last_state = lgpio.gpio_read(self.chip, RAIN_SENSOR_PIN)
        except Exception:
            last_state = 1
        last_time = 0.0
        debounce_s = BOUNCE_TIME / 1000.0
        while not self._stop:
            try:
                state = lgpio.gpio_read(self.chip, RAIN_SENSOR_PIN)
                now = time.time()
                # Flanco de bajada (pulso)
                if last_state == 1 and state == 0:
                    if (now - last_time) >= debounce_s:
                        self.tip_callback()
                        last_time = now
                last_state = state
                time.sleep(0.005)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"RainSensor monitor error: {e}")
                time.sleep(0.1)

    def reset(self):
        """Reinicia contadores de lluvia de forma atómica."""
        with self._lock:
            self.tips = 0
            self.accumulated = 0.0

    def close(self):
        """Detiene el hilo de monitoreo y libera recursos GPIO."""
        self._stop = True
        try:
            if hasattr(self, '_monitor_thread') and self._monitor_thread:
                self._monitor_thread.join(timeout=0.5)
        except Exception:
            pass
        if getattr(self, 'chip', None) is not None:
            try:
                lgpio.gpiochip_close(self.chip)
            except Exception:
                pass

    # Eliminado: el guardado ahora lo gestiona BlockStorage desde el manager
