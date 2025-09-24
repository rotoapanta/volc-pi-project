import serial
import threading
import glob
import os
import time
from utils.sensors.seismic_utils import parse_seismic_message
from config import STATION_NAME, IDENTIFIER, SEISMIC_MODEL, SEISMIC_SERIAL_NUMBER
from utils.log_utils import setup_logger
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
        self.ser = None
        # Intervalo de adquisición específico para este sensor
        self.interval_minutes = interval_minutes
        # Parámetros de robustez de lectura/reconexión
        self.max_reconnect_attempts = 3
        self.read_attempts = 5
        self.read_delay = 0.2
        self.backoff_factor = 2.0
        self.max_backoff = 2.0
        # Instancia el almacenamiento genérico para sísmico
        # Eliminado: el almacenamiento ahora lo gestiona BlockStorage desde el manager

    def _open_serial(self):
        """Abre el puerto serial con timeout, con manejo de errores."""
        try:
            if self.ser and getattr(self.ser, "is_open", False):
                return
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        except Exception as e:
            logger.error(f"Fallo al abrir puerto sísmico {self.port}: {e}")
            raise

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
        self._open_serial()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        while not self._stop_event.is_set():
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                if line and self.callback:
                    self.callback(line)
            except Exception as e:
                logger.error(f"Error leyendo sensor sísmico (read_loop): {e}")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        if self.ser:
            self.ser.close()

    def acquire(self):
        """Lee una línea del sensor sísmico con reintentos y reconexión si es necesario."""
        # Asegurar puerto abierto
        try:
            if self.ser is None or not getattr(self.ser, "is_open", False):
                self._open_serial()
        except Exception:
            # No se pudo abrir al primer intento
            pass

        attempts_left = self.read_attempts
        reconnects_left = self.max_reconnect_attempts
        delay = self.read_delay

        while attempts_left > 0:
            try:
                if self.ser is None or not getattr(self.ser, "is_open", False):
                    if reconnects_left <= 0:
                        logger.warning("No se recibió dato sísmico: sin puerto serial tras reintentos")
                        return None
                    try:
                        self._open_serial()
                    except Exception:
                        reconnects_left -= 1
                        time.sleep(delay)
                        delay = min(delay * self.backoff_factor, self.max_backoff)
                        continue

                line = self.ser.readline().decode(errors='ignore').strip()
                if line:
                    return line
                attempts_left -= 1
                time.sleep(delay)
                delay = min(delay * self.backoff_factor, self.max_backoff)
            except Exception as e:
                logger.error(f"Error leyendo sensor sísmico; intentando reconectar: {e}")
                # Cerrar y reintentar abrir
                try:
                    if self.ser:
                        self.ser.close()
                except Exception:
                    pass
                self.ser = None
                reconnects_left -= 1
                if reconnects_left < 0:
                    logger.warning("No se recibió dato sísmico tras reintentos")
                    return None
                time.sleep(delay)
                delay = min(delay * self.backoff_factor, self.max_backoff)
                # Intentará reabrir en la siguiente iteración
        logger.warning("No se recibió dato sísmico (timeout de lectura)")
        return None

    def process(self, raw, fecha, tiempo, latitud=None, longitud=None, altura=None, voltage=None):
        """Procesa la línea cruda del sensor sísmico usando la función centralizada."""
        return parse_seismic_message(raw, fecha, tiempo, latitud=latitud, longitud=longitud, altura=altura, voltage=voltage)

    # Eliminado: el guardado ahora lo gestiona BlockStorage desde el manager
