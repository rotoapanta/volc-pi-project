from .base_sensor import BaseSensor
import time
import os
import json
from utils.storage.storage_utils import get_dta_path

class RainSensor(BaseSensor):
    def __init__(self, config, logger=None):
        super().__init__(config, logger)
        self.tips = 0
        self.accumulated = 0.0
        # Aquí puedes inicializar el hardware real (GPIO, interrupciones, etc.)
        # Por ejemplo:
        # import RPi.GPIO as GPIO
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(config["pin"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # GPIO.add_event_detect(config["pin"], GPIO.FALLING, callback=self.tip_callback, bouncetime=50)

    def tip_callback(self, channel=None):
        self.tips += 1
        self.accumulated += 0.25
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[PLUVIOMETER] TIME={timestamp} TIPS={self.tips:02d} ACCUMULATED_RAIN={self.accumulated:.2f}mm"
        if self.logger:
            self.logger.info(msg)

    def acquire(self):
        # Si usas interrupciones, este método puede ser vacío o solo retornar el acumulado cada intervalo
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

    # Eliminado: el guardado ahora lo gestiona BlockStorage desde el manager
