import os
import json
from datetime import datetime, timedelta
from config import STATION_NAME, IDENTIFIER, SEISMIC_STATION_TYPE, SEISMIC_MODEL, SEISMIC_SERIAL_NUMBER
from utils.storage_utils import get_dta_path

def parse_seismic_message(msg, latitud=None, longitud=None, altura=None):
    """
    Parsea y explica un mensaje sísmico tipo:
    [SEISMIC] 007 +0013 +0010 +0050 +3277 c+1379
    Devuelve un dict con los valores extraídos.
    """
    if msg.startswith("[SEISMIC]"):
        msg = msg.replace("[SEISMIC]", "").strip()
    parts = msg.split()
    if len(parts) < 6:
        return None
    st = parts[0]
    pasa_banda = parts[1]
    pasa_bajo = parts[2]
    pasa_alto = parts[3]
    bateria = parts[4]
    cks = parts[5]
    try:
        st_num = int(st)
        pasa_banda_raw = int(pasa_banda)
        pasa_bajo_raw = int(pasa_bajo)
        pasa_alto_raw = int(pasa_alto)
        bateria_raw = int(bateria)
    except Exception:
        return None
    result = {
        "estacion": f"{st_num:03d}",
        "pasa_banda": f"{pasa_banda_raw:04d}",
        "pasa_bajo": f"{pasa_bajo_raw:04d}",
        "pasa_alto": f"{pasa_alto_raw:04d}",
        "bateria": f"{bateria_raw}"
    }
    if latitud is not None:
        result["latitud"] = latitud
    if longitud is not None:
        result["longitud"] = longitud
    if altura is not None:
        result["altura"] = altura
    return result

def save_seismic_data(msg, fecha, tiempo, latitud=None, longitud=None, altura=None):
    """
    Guarda los datos sísmicos en formato JSON igual que los datos de pluviometría.
    """
    datos = parse_seismic_message(msg, latitud=latitud, longitud=longitud, altura=altura)
    if not datos:
        return False
    # Estructura de lectura
    lectura = {
        "FECHA": fecha,
        "TIEMPO": tiempo,
        "DATOS": datos
    }
    # Ruta y nombre de archivo
    dta_path = get_dta_path(fecha)
    file_date = fecha.replace("-", "")
    hour_str = tiempo[:2] + "00"
    filename = os.path.join(dta_path, f"EC.{STATION_NAME}.{SEISMIC_STATION_TYPE}_{SEISMIC_MODEL}_{SEISMIC_SERIAL_NUMBER}_{file_date}_{hour_str}.json")
    # Estructura base
    base = {
        "TIPO": SEISMIC_STATION_TYPE,
        "NOMBRE": STATION_NAME,
        "IDENTIFICADOR": IDENTIFIER,
        "LECTURAS": []
    }
    # Leer si existe
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                base = json.load(f)
            except Exception:
                pass
    # Evitar duplicados
    if not any(l["TIEMPO"] == tiempo for l in base["LECTURAS"]):
        base["LECTURAS"].append(lectura)
    # Guardar
    with open(filename, 'w') as f:
        json.dump(base, f, indent=4)
    try:
        from utils.print_utils import print_colored
        print_colored(f"[ OK ] Datos sísmicos guardados: {filename}")
    except Exception:
        print(f"[ OK ] Datos sísmicos guardados: {filename}")
    return True

class SeismicDataAccumulator:
    def __init__(self, acquisition_interval=1):
        self.acquisition_interval = acquisition_interval  # minutos
        self.data_accumulator = {}
        self.last_saved_time = None

    def get_current_interval_end(self):
        now = datetime.now()
        minutes = (now.minute // self.acquisition_interval) * self.acquisition_interval
        current_end = now.replace(minute=minutes, second=0, microsecond=0)
        return current_end.strftime("%H:%M:00"), now.strftime("%Y-%m-%d")

    def accumulate_and_save(self, msg, latitud=None, longitud=None, altura=None):
        tiempo, fecha = self.get_current_interval_end()
        # Solo guardar una vez por intervalo
        if self.last_saved_time != (fecha, tiempo):
            save_seismic_data(msg, fecha, tiempo, latitud=latitud, longitud=longitud, altura=altura)
            self.last_saved_time = (fecha, tiempo)
