import os
import json
import threading
from datetime import datetime
from utils.log_utils import setup_logger

class BlockStorage:
    def __init__(self, station_name, identifier, model, serial_number, logger=None, output_dir=None, block_type='hour', tipo="GENERIC", interval_minutes=1, extractor_func=None):
        self.station_name = station_name
        self.identifier = identifier
        self.model = model
        self.serial_number = serial_number
        self.tipo = tipo
        # Usa el logger pasado o crea uno estándar con setup_logger
        if logger is not None:
            self.logger = logger
        else:
            self.logger = setup_logger("block_storage", log_file="block_storage.log")
        self.output_dir = output_dir
        self.block_type = block_type  # 'hour', 'day', etc.
        self.current_block = None
        self.block_data = []
        self.interval_minutes = interval_minutes
        self.extractor_func = extractor_func
        self.data_accumulator = {}
        self._lock = threading.RLock()

    def get_block_start(self, dt):
        if self.block_type == 'hour':
            return dt.replace(minute=0, second=0, microsecond=0)
        elif self.block_type == 'day':
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        # Puedes agregar más tipos si lo necesitas
        return dt

    def add_data(self, raw):
        self._lock.acquire()
        try:
            now = datetime.now()
            block_start = self.get_block_start(now)
            # Guardar el dato crudo relevante (sin loguear en logger)
            if self.current_block and self.current_block != block_start:
                self.save_block_file(self.current_block, self.block_data)
                self.block_data = []
            self.current_block = block_start
            # Usar extractor_func si está definido, si no, guardar raw como está
            if self.extractor_func:
                data = self.extractor_func(raw, now)
            else:
                data = raw
            if data:
                # Guardar solo la última lectura por bloque de interval_minutes minutos
                minuto = int(data["TIEMPO"][3:5])
                bloque = (minuto // self.interval_minutes) * self.interval_minutes
                idx = next((i for i, d in enumerate(self.block_data)
                            if d["FECHA"] == data["FECHA"] and
                               int(d["TIEMPO"][3:5]) // self.interval_minutes == minuto // self.interval_minutes and
                               d["TIEMPO"][:2] == data["TIEMPO"][:2]), None)
                if idx is not None:
                    self.block_data[idx] = data  # Sobrescribe la lectura previa de ese bloque
                else:
                    self.block_data.append(data)
                # Guardar en disco en tiempo real
                self.save_block_file(self.current_block, self.block_data)
        finally:
            self._lock.release()

    def save_block_file(self, block_start, data):
        self._lock.acquire()
        try:
            # El nombre del archivo depende del tipo de bloque
            if self.block_type == 'hour':
                date_part = block_start.strftime("%Y%m%d")
                hour_part = block_start.strftime("%H00")
            elif self.block_type == 'day':
                date_part = block_start.strftime("%Y%m%d")
                hour_part = "0000"
            else:
                date_part = block_start.strftime("%Y%m%d")
                hour_part = block_start.strftime("%H%M")
            # Crea subcarpetas por año/mes/día automáticamente
            year = block_start.strftime("%Y")
            month = block_start.strftime("%m")
            day = block_start.strftime("%d")
            output_dir = os.path.join(self.output_dir, year, month, day)
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(
                output_dir,
                f"EC.{self.station_name}.{self.tipo}_{self.model}_{self.serial_number}_{date_part}_{hour_part}.json"
            )
            file_data = {
                "TIPO": self.tipo,
                "NOMBRE": self.station_name,
                "IDENTIFICADOR": self.identifier,
                "LECTURAS": data
            }
            tmp_filename = filename + ".tmp"
            with open(tmp_filename, "w") as f:
                json.dump(file_data, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_filename, filename)
            try:
                dir_fd = os.open(output_dir, os.O_DIRECTORY)
                os.fsync(dir_fd)
                os.close(dir_fd)
            except Exception:
                pass
            self.logger.info(f"{self.tipo} data saved: {filename}")
        finally:
            self._lock.release()

    def flush(self):
        self._lock.acquire()
        try:
            if self.block_data:
                self.save_block_file(self.current_block, self.block_data)
                self.block_data = []
        finally:
            self._lock.release()

    # --- Métodos de acumulación (fusionados de GenericDataStorage) ---
    def get_current_interval_end(self, acquisition_interval=2):
        from datetime import datetime, timedelta
        now = datetime.now()
        minutes = (now.minute // acquisition_interval) * acquisition_interval
        current_end = now.replace(minute=minutes, second=0, microsecond=0)
        if now >= current_end + timedelta(minutes=acquisition_interval):
            current_end += timedelta(minutes=acquisition_interval)
        return current_end.strftime("%H:%M:00")

    def accumulate(self, data, acquisition_interval=2):
        import time
        date_str = time.strftime("%Y-%m-%d", time.localtime())
        interval_end_str = self.get_current_interval_end(acquisition_interval)
        if interval_end_str not in self.data_accumulator:
            self.data_accumulator[interval_end_str] = {
                "FECHA": date_str,
                "TIEMPO": interval_end_str,
                "DATOS": []
            }
        self.data_accumulator[interval_end_str]["DATOS"].append(data)
        saved_files = self.save_accumulated_data()
        return saved_files

    def save_accumulated_data(self):
        from utils.storage.storage_utils import get_dta_path
        saved_files = []
        self._lock.acquire()
        try:
            for interval_end_str, entry in self.data_accumulator.items():
                date_str = entry["FECHA"]
                time_str = entry["TIEMPO"]
                hour_str = time_str[:2] + "00"
                directory = get_dta_path(date_str)
                file_date = date_str.replace("-", "")
                tipo_sufijo = "SIS" if self.tipo.upper().startswith("SISM") else "RGA"
                filename = os.path.join(directory, f"EC.{self.station_name}.{tipo_sufijo}_{self.model}_{self.serial_number}_{file_date}_{hour_str}.json")

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
                    os.makedirs(directory, exist_ok=True)
                    tmp = filename + ".tmp"
                    with open(tmp, 'w') as file:
                        json.dump(data, file, indent=4)
                        file.flush()
                        os.fsync(file.fileno())
                    os.replace(tmp, filename)
                    try:
                        dir_fd = os.open(directory, os.O_DIRECTORY)
                        os.fsync(dir_fd)
                        os.close(dir_fd)
                    except Exception:
                        pass
                    saved_files.append(filename)
                except Exception as e:
                    print(f"Error al guardar datos: {e}")

            self.data_accumulator = {}
            return saved_files
        finally:
            self._lock.release()

    def create_empty_structure(self):
        return {
            "TIPO": self.tipo,
            "NOMBRE": self.station_name,
            "IDENTIFICADOR": self.identifier,
            "LECTURAS": []
        }

    def set_output_dir(self, new_output_dir):
        """
        Cambia la ruta de almacenamiento y guarda los datos actuales en la nueva ubicación.
        Operación atómica con lock para evitar rutas inconsistentes durante escrituras concurrentes.
        """
        self._lock.acquire()
        try:
            self.output_dir = new_output_dir
            self.logger.info(f"Ruta de almacenamiento cambiada a: {new_output_dir}")
            # Guardado inmediato en la nueva ubicación
            self.flush()
        finally:
            self._lock.release()
