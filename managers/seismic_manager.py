import time
from sensors.seismic import SeismicSensor
from utils.extractors.data_extractors import extract_seismic
from utils.log_utils import setup_logger
import os

from datetime import datetime, timedelta

class SeismicManager:
    def __init__(self, config, logger=None, storage=None):
        # Inicialización del sensor sísmico
        self.sensor = SeismicSensor(
            port=config.get("port"),
            baudrate=config.get("baudrate")
        )
        # Logger profesional y consistente
        self.logger = setup_logger("seismic", log_file="seismic.log")
        self.storage = storage
        self.interval = config.get('interval', 60)  # segundos

    def wait_until_next_minute(self):
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        wait_seconds = (next_minute - now).total_seconds()
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    def run(self):
        self.wait_until_next_minute()  # Espera hasta el próximo minuto exacto
        while True:
            # 1. Adquisición del dato crudo
            raw = self.sensor.acquire()
            # 2. Obtener datos de GPS
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
                        self.logger.info("Dato GPS no válido en seismic_manager (lat/lon/alt None)")
                    else:
                        msg = f"Dato GPS recibido en seismic_manager: lat: {gps_data['LATITUD']} lon: {gps_data['LONGITUD']} alt: {gps_data['ALTURA']}"
                        self.logger.info(msg)
            except Exception:
                pass
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
            if raw:
                parts = raw.strip().split()
                if len(parts) >= 4:
                    raw_dict = {
                        "PASA_BANDA": parts[1].replace('+', ''),
                        "PASA_BAJO": parts[2].replace('+', ''),
                        "PASA_ALTO": parts[3].replace('+', ''),
                        "LATITUD": gps_data["LATITUD"],
                        "LONGITUD": gps_data["LONGITUD"],
                        "ALTURA": gps_data["ALTURA"],
                        "BATERIA": battery
                    }
                    # 5. Log y almacenamiento
                    seismic_msg = f"PASA_BANDA={raw_dict['PASA_BANDA']} PASA_BAJO={raw_dict['PASA_BAJO']} PASA_ALTO={raw_dict['PASA_ALTO']}"
                    self.logger.info(seismic_msg)
                    self.storage.add_data(raw_dict)
                    self.logger.info(f"Datos sísmicos guardados")
            time.sleep(self.interval)
