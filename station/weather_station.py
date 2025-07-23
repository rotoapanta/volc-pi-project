import os
import time
import json
from datetime import datetime, timedelta

from config import *
from sensors.rain import RainSensor
from utils.leds_utils import LEDManager
from utils.storage_utils import get_dta_path
from utils.battery_utils import BatteryMonitor

class WeatherStation:
    def __init__(self, station_name, identifier, acquisition_interval, leds, logger):
        self.station_name = station_name
        self.identifier = identifier
        self.acquisition_interval = acquisition_interval
        self.rainfall_count = 0
        self.rainfall_accumulated = 0.0
        self.last_interval_end_str = None
        self.data_accumulator = {}

        self.leds = leds
        self.logger = logger
        self.rain_sensor = RainSensor(RAIN_SENSOR_PIN, BOUNCE_TIME, self.count_rainfall)
        self.battery_monitor = BatteryMonitor()

    def count_rainfall(self):
        self.rainfall_count += 1
        self.rainfall_accumulated += 0.25
        timestamp = self.get_timestamp()
        print(f"[DEBUG] Pulso pluviómetro detectado en {timestamp} (tip #{self.rainfall_count})")
        self.logger.info(f"Impulso detectado: {self.rainfall_count} tips, {self.rainfall_accumulated:.2f} mm acumulados a las {timestamp}")
        self.leds.blink("TX")

    def get_timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def get_current_interval_end(self):
        now = datetime.now()
        minutes = (now.minute // self.acquisition_interval) * self.acquisition_interval
        current_end = now.replace(minute=minutes, second=0, microsecond=0)
        if now >= current_end + timedelta(minutes=self.acquisition_interval):
            current_end += timedelta(minutes=self.acquisition_interval)
        return current_end.strftime("%H:%M:00")

    def log_rainfall(self, date_str, interval_end_str, rainfall_mm):
        if interval_end_str not in self.data_accumulator:
            voltage = self.battery_monitor.read_all()["voltage"]
            self.data_accumulator[interval_end_str] = {
                "FECHA": date_str,
                "TIEMPO": interval_end_str,
                "NIVEL": rainfall_mm,
                "BATERIA": voltage
            }
            self.save_accumulated_data()

    def save_accumulated_data(self):
        for interval_end_str, entry in self.data_accumulator.items():
            date_str = entry["FECHA"]
            time_str = entry["TIEMPO"]
            hour_str = time_str[:2] + "00"
            directory = get_dta_path(date_str)
            file_date = date_str.replace("-", "")
            filename = os.path.join(directory, f"EC.{self.station_name}.{TIPO_ESTACION}_{MODEL}_{SERIAL_NUMBER}_{file_date}_{hour_str}.json")

            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        data = self.create_empty_structure()
            else:
                data = self.create_empty_structure()

            if not any(interval_end_str == lectura["TIEMPO"] for lectura in data["LECTURAS"]):
                data["LECTURAS"].append(entry)

            try:
                with open(filename, 'w') as file:
                    json.dump(data, file, indent=4)
                self.logger.info(f"✅ Datos guardados: {filename}")
            except Exception as e:
                self.logger.error(f"Error al guardar datos: {e}")
                self.leds.set("ERROR", True)

        self.data_accumulator = {}

    def create_empty_structure(self):
        return {
            "TIPO": "PLUVIOMETRIA",
            "NOMBRE": self.station_name,
            "IDENTIFICADOR": self.identifier,
            "LECTURAS": []
        }

    def check_inactivity(self):
        current_interval_end_str = self.get_current_interval_end()
        date_str = time.strftime("%Y-%m-%d", time.localtime())
        if self.last_interval_end_str is None or self.last_interval_end_str != current_interval_end_str:
            if self.rainfall_accumulated > 0:
                self.log_rainfall(date_str, current_interval_end_str, self.rainfall_accumulated)
                self.logger.info(f"💧 Lluvia registrada: {self.rainfall_accumulated:.2f} mm en {current_interval_end_str}")
            else:
                self.log_rainfall(date_str, current_interval_end_str, 0.0)
                self.logger.info(f"⏳ Sin lluvia. Registrado 0.0 mm para {current_interval_end_str}")
            self.rainfall_accumulated = 0.0
            self.rainfall_count = 0
            self.last_interval_end_str = current_interval_end_str

    def cleanup(self):
        self.rain_sensor.cleanup()
        self.logger.info("GPIO limpio, estación detenida.")

    def run(self):
        try:
            self.rain_sensor.setup()
            self.leds.heartbeat()
            self.logger.info(f"🌧️ Estación activa: {self.station_name} - Intervalo de adquisición: {self.acquisition_interval} min")
            while True:
                time.sleep(1)
                self.check_inactivity()
        except KeyboardInterrupt:
            self.logger.warning("🛑 Interrupción manual recibida. Cerrando estación.")
            self.cleanup()
        except Exception as e:
            self.logger.error(f"⚠️ Error inesperado: {e}")
            self.leds.set("ERROR", True)
            self.cleanup()
