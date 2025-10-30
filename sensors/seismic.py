import threading
import glob
import os
import time
from utils.sensors.seismic_utils import parse_seismic_message
from config import STATION_NAME, IDENTIFIER, SEISMIC_MODEL, SEISMIC_SERIAL_NUMBER
from utils.log_utils import setup_logger
from sensors.serial_port import RobustSerial
logger = setup_logger("seismic_sensor", log_file="seismic.log")

from datetime import datetime

class SeismicSensor:
    def __init__(self, port=None, baudrate=9600, callback=None, interval_minutes=1):
        # Si no se especifica puerto, busca automáticamente en /dev/serial/by-id/
        if port is None:
            by_id = glob.glob('/dev/serial/by-id/*')
            if by_id:
                self.port = by_id[0]
                # logger.info(f"[INFO] Usando puerto sísmico: {self.port}")
            else:
                logger.error("No se encontró ningún dispositivo USB-Serial en /dev/serial/by-id/")
                raise RuntimeError("No se encontró ningún dispositivo USB-Serial en /dev/serial/by-id/")
        else:
            self.port = port
        self.baudrate = baudrate
        # Si no se pasa callback, usar el interno por defecto
        self.callback = callback if callback is not None else self.on_seismic_data
        self._stop_event = threading.Event()
        self._thread = None
        # Intervalo de adquisición específico para este sensor
        self.interval_minutes = interval_minutes
        # Parámetros de robustez de lectura/reconexión
        self.read_attempts = 5
        self.read_delay = 0.2
        self.backoff_factor = 2.0
        self.max_backoff = 2.0
        # Serial robusto compartido
        self.rs = RobustSerial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=1,
            logger=logger,
            max_open_failures=5,
            open_cooldown_seconds=30,
            read_delay=self.read_delay,
            backoff_factor=self.backoff_factor,
            max_backoff=self.max_backoff,
        )
        # Eliminado: el almacenamiento ahora lo gestiona BlockStorage desde el manager

    def _open_serial(self):
        """Abre el puerto serial mediante RobustSerial; lanza excepción si no se puede abrir."""
        if not self.rs.open():
            raise RuntimeError(f"No se pudo abrir puerto sísmico {self.port}")

    def on_seismic_data(self, raw_data):
        """Callback para procesar y almacenar datos sísmicos crudos."""
        now = datetime.now()
        minutes = (now.minute // self.interval_minutes) * self.interval_minutes
        interval_end = now.replace(minute=minutes, second=0, microsecond=0)
        fecha = interval_end.strftime("%Y-%m-%d")
        tiempo = interval_end.strftime("%H:%M:00")
        # Aquí podrías obtener latitud, longitud, altura, voltage si están disponibles
        data_structured = self.process(
            raw_data,
            fecha,
            tiempo,
            latitud=None,
            longitud=None,
            altura=None,
            voltage=None
        )
        # Eliminado: el guardado ahora lo gestiona BlockStorage desde el manager

    def start(self):
        # Evitar múltiples hilos de lectura
        if getattr(self, "_thread", None) and self._thread.is_alive():
            return
        self._stop_event.clear()
        try:
            self._open_serial()
        except Exception:
            # Se reintentará en el bucle de lectura con backoff
            pass
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        """Hilo lector con reconexión robusta y backoff en caso de error."""
        delay = self.read_delay
        while not self._stop_event.is_set():
            # Asegurar que el puerto está abierto (RobustSerial ya maneja cooldown)
            if not self.rs.is_open():
                try:
                    self._open_serial()
                    delay = self.read_delay
                except Exception as e:
                    # El logger interno ya registró el fallo
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_backoff)
                    continue
            # Leer dato
            data = self.rs.readline()
            if not data:
                time.sleep(0.05)
                continue
            try:
                line = data.decode('utf-8', errors='ignore').strip()
            except Exception:
                line = str(data, errors='ignore').strip()
            if line and self.callback:
                self.callback(line)
            delay = self.read_delay

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        try:
            self.rs.close()
        except Exception:
            pass

    def acquire(self):
        """Lee una línea del sensor sísmico con reintentos y reconexión si es necesario."""
        # Asegurar puerto abierto
        # Intento de lectura con reintentos mínimos; RobustSerial maneja reconexiones
        attempts_left = self.read_attempts
        delay = self.read_delay
        while attempts_left > 0:
            data = self.rs.readline()
            if data:
                try:
                    return data.decode(errors='ignore').strip()
                except Exception:
                    return str(data, errors='ignore').strip()
            attempts_left -= 1
            time.sleep(delay)
            delay = min(delay * self.backoff_factor, self.max_backoff)
        logger.warning("No se recibió dato sísmico (timeout de lectura)")
        return None

    def process(self, raw, fecha, tiempo, latitud=None, longitud=None, altura=None, voltage=None):
        """Procesa la línea cruda del sensor sísmico usando la función centralizada."""
        return parse_seismic_message(raw, fecha, tiempo, latitud=latitud, longitud=longitud, altura=altura, voltage=voltage)

    # Eliminado: el guardado ahora lo gestiona BlockStorage desde el manager
