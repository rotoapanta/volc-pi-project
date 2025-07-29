import os
import json
import time
from utils.storage_utils import get_dta_path
from config import STATION_NAME, IDENTIFIER, MODEL, SERIAL_NUMBER

TIPO_ESTACION = "SIS"  # Sismico

class SeismicDataAccumulator:
    def __init__(self):
        self.data_accumulator = {}

    def get_current_interval_end(self, acquisition_interval=2):
        # Por defecto, intervalo de 2 minutos (ajustar si es necesario)
        from datetime import datetime, timedelta
        now = datetime.now()
        minutes = (now.minute // acquisition_interval) * acquisition_interval
        current_end = now.replace(minute=minutes, second=0, microsecond=0)
        if now >= current_end + timedelta(minutes=acquisition_interval):
            current_end += timedelta(minutes=acquisition_interval)
        return current_end.strftime("%H:%M:00")

    def accumulate(self, data, acquisition_interval=2):
        date_str = time.strftime("%Y-%m-%d", time.localtime())
        interval_end_str = self.get_current_interval_end(acquisition_interval)
        if interval_end_str not in self.data_accumulator:
            self.data_accumulator[interval_end_str] = {
                "FECHA": date_str,
                "TIEMPO": interval_end_str,
                "DATOS": []
            }
        self.data_accumulator[interval_end_str]["DATOS"].append(data)
        self.save_accumulated_data()

    def save_accumulated_data(self):
        for interval_end_str, entry in self.data_accumulator.items():
            date_str = entry["FECHA"]
            time_str = entry["TIEMPO"]
            hour_str = time_str[:2] + "00"
            directory = get_dta_path(date_str)
            file_date = date_str.replace("-", "")
            filename = os.path.join(directory, f"EC.{STATION_NAME}.SIS_{MODEL}_{SERIAL_NUMBER}_{file_date}_{hour_str}.json")

            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        data = self.create_empty_structure()
            else:
                data = self.create_empty_structure()

            # Evita duplicados por intervalo
            if not any(interval_end_str == lectura["TIEMPO"] for lectura in data["LECTURAS"]):
                data["LECTURAS"].append(entry)

            try:
                with open(filename, 'w') as file:
                    json.dump(data, file, indent=4)
            except Exception as e:
                from utils.print_utils import print_colored
                print_colored(f"[ERROR] Error al guardar datos sísmicos: {e}")

        self.data_accumulator = {}

    def create_empty_structure(self):
        return {
            "TIPO": "SISMICO",
            "NOMBRE": STATION_NAME,
            "IDENTIFICADOR": IDENTIFIER,
            "LECTURAS": []
        }
