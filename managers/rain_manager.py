import time
from sensors.rain import RainSensor
from utils.extractors.data_extractors import extract_rain
from utils.log_utils import log_and_print, setup_logger
import os

from datetime import datetime, timedelta

class RainManager:
    def __init__(self, config, logger=None, storage=None):
        # Inicialización del sensor de lluvia
        self.sensor = RainSensor(config, logger)
        # Logger profesional y consistente
        self.logger = setup_logger("rain", log_file="rain.log")
        self.storage = storage
        self.interval = config.get('interval', 60)  # segundos

    def wait_until_next_minute(self):
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        wait_seconds = (next_minute - now).total_seconds()
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    def run(self):
        next_time = time.time()
        while True:
            # 1. Adquisición del dato crudo
            nivel = self.sensor.acquire()
            # 2. Obtener datos de GPS y batería
            gps_data = {"LATITUD": None, "LONGITUD": None, "ALTURA": None}
            battery = None
            try:
                from managers.gps_manager import get_last_gps_data
                gps = get_last_gps_data()
                gps_data["LATITUD"] = gps.get("lat")
                gps_data["LONGITUD"] = gps.get("lon")
                gps_data["ALTURA"] = gps.get("alt")
                # Log de dato GPS solo en el logger principal
                if self.logger:
                    if gps_data['LATITUD'] is None or gps_data['LONGITUD'] is None or gps_data['ALTURA'] is None:
                        self.logger.info("Dato GPS no válido en rain_manager (lat/lon/alt None)")
                    else:
                        msg = f"Dato GPS recibido en rain_manager: lat: {gps_data['LATITUD']} | lon: {gps_data['LONGITUD']} | alt: {gps_data['ALTURA']}"
                        self.logger.info(msg)
            except Exception as e:
                if hasattr(self, 'gps_logger'):
                    self.gps_logger.error(f"[GPS][ERROR] {e}")
            # 3. Obtener voltaje de batería            
            try:
                from utils.sensors.battery_utils import BatteryMonitor
                battery_monitor = BatteryMonitor()
                battery_info = battery_monitor.read_all()
                battery_monitor.close()
                battery = battery_info["voltage"]
            except Exception:
                battery = None
            # 4. Procesamiento, log y almacenamiento
            raw = {
                "NIVEL": nivel,
                "LATITUD": gps_data["LATITUD"],
                "LONGITUD": gps_data["LONGITUD"],
                "ALTURA": gps_data["ALTURA"],
                "BATERIA": battery
            }
            # 5. Log y almacenamiento
            rain_msg = f"Nivel: {raw['NIVEL']} mm"
            self.logger.info(rain_msg)
            self.storage.add_data(raw)
            # Reiniciar acumulado para el siguiente intervalo
            try:
                self.sensor.reset()
            except Exception:
                pass
            self.logger.info(f"Datos lluvia guardados")
            # Calcular el tiempo hasta el próximo ciclo
            next_time += self.interval
            sleep_time = max(0, next_time - time.time())
            time.sleep(sleep_time)