import time
import os
import re
from datetime import datetime, timedelta

from sensors.seismic import SeismicSensor
from utils.extractors.data_extractors import extract_seismic  # Mantener import por compatibilidad
from utils.log_utils import setup_logger


class SeismicManager:
    def __init__(self, config, logger=None, storage=None):
        # Inicialización del sensor sísmico
        self.sensor = SeismicSensor(
            port=config.get("port"),
            baudrate=config.get("baudrate")
        )
        # Logger profesional y consistente (usar el del sistema si lo pasan)
        self.logger = logger if logger is not None else setup_logger("seismic", log_file="seismic.log")
        self.storage = storage
        self.interval = config.get('interval', 60)  # segundos

    def wait_until_next_minute(self):
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        wait_seconds = (next_minute - now).total_seconds()
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    def _parse_and_validate(self, raw):
        """Valida y parsea el frame sísmico. Devuelve dict o None si inválido.
        Formato esperado (flexible):
        [SEISMIC] ST +#### +#### +#### [BAT] [c+####]
        - ST, PASA_* numéricos
        - BAT opcional en mV (entero)
        - checksum opcional con patrón c[+|-]?d+
        """
        if not raw:
            return None
        try:
            msg = raw.strip()
            if msg.startswith('[SEISMIC]'):
                msg = msg[len('[SEISMIC]'):].strip()
            parts = msg.split()
            if len(parts) < 4:
                self.logger.warning(f"Frame sísmico inválido (campos insuficientes): {raw}")
                return None

            st_s, pb_s, pl_s, pa_s = parts[0], parts[1], parts[2], parts[3]

            def to_int4(x):
                v = int(x.replace('+', ''))
                if v < 0 or v > 9999:
                    raise ValueError("valor fuera de rango")
                return v

            # Validación de ST (no se usa, solo validar número)
            _ = int(st_s.replace('+', ''))
            pb = to_int4(pb_s)
            pl = to_int4(pl_s)
            pa = to_int4(pa_s)

            bat_mv = None
            cks_ok = True

            # Campo 5 puede ser BAT o checksum
            if len(parts) >= 5:
                p5 = parts[4]
                if re.match(r'^[cC][+-]?\d+$', p5):
                    # Es checksum, ok
                    pass
                else:
                    # Intentar batería en mV
                    b = p5.replace('+', '')
                    if b.lstrip('-').isdigit():
                        bat_mv = int(b)
                        if bat_mv < 0 or bat_mv > 10000:
                            self.logger.warning(f"Batería en frame fuera de rango (mV): {bat_mv}")
                            bat_mv = None
                    else:
                        self.logger.warning(f"Campo desconocido en posición 5: {p5}")

            # Campo 6 si existe, debe ser checksum
            if len(parts) >= 6:
                cks = parts[5]
                if not re.match(r'^[cC][+-]?\d+$', cks):
                    self.logger.warning(f"Checksum con formato inválido: {cks}")
                    cks_ok = False

            if not cks_ok:
                return None

            return {
                "pasa_banda": pb,
                "pasa_bajo": pl,
                "pasa_alto": pa,
                "bat_mv": bat_mv,
            }
        except Exception as e:
            self.logger.warning(f"Error parseando frame sísmico: {e}; raw: {raw}")
            return None

    def run(self):
        next_time = time.time()
        while True:
            start_time = time.time()
            # 1. Adquisición del dato crudo (con reintentos/reconexión dentro del sensor)
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
                if self.logger:
                    if gps_data['LATITUD'] is None or gps_data['LONGITUD'] is None or gps_data['ALTURA'] is None:
                        self.logger.info("Dato GPS no válido en seismic_manager (lat/lon/alt None)")
                    else:
                        msg = (
                            f"Dato GPS recibido en seismic_manager: lat: {gps_data['LATITUD']} | "
                            f"lon: {gps_data['LONGITUD']} | alt: {gps_data['ALTURA']}"
                        )
                        self.logger.info(msg)
            except Exception:
                pass

            # 3. Obtener voltaje de batería (ADC)
            try:
                from utils.sensors.battery_utils import BatteryMonitor
                battery_monitor = BatteryMonitor()
                battery_info = battery_monitor.read_all()
                battery_monitor.close()
                battery = battery_info["voltage"]
            except Exception:
                battery = None

            # 4. Procesamiento, validación, log y almacenamiento
            if raw:
                parsed = self._parse_and_validate(raw)
                if parsed is None:
                    # Frame inválido; no guardar
                    pass
                else:
                    # Unificar fuente de batería: solo usar ADC (BatteryMonitor)
                    bat_v = battery

                    raw_dict = {
                        "PASA_BANDA": f"{parsed['pasa_banda']:04d}",
                        "PASA_BAJO": f"{parsed['pasa_bajo']:04d}",
                        "PASA_ALTO": f"{parsed['pasa_alto']:04d}",
                        "LATITUD": gps_data["LATITUD"],
                        "LONGITUD": gps_data["LONGITUD"],
                        "ALTURA": gps_data["ALTURA"],
                        "BATERIA": bat_v,
                    }

                    seismic_msg = (
                        f"Pasa Banda: {raw_dict['PASA_BANDA']} | "
                        f"Pasa Bajo: {raw_dict['PASA_BAJO']} | "
                        f"Pasa Alto: {raw_dict['PASA_ALTO']}"
                    )
                    self.logger.info(seismic_msg)
                    self.storage.add_data(raw_dict)
                    self.logger.info("Datos sísmicos guardados")

            # 5. Calcular el tiempo hasta el próximo ciclo
            next_time += self.interval
            sleep_time = max(0, next_time - time.time())
            time.sleep(sleep_time)
