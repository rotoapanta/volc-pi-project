# sensors/gps.py

import serial
import threading
from config import GPS_PORT, GPS_BAUDRATE, GPS_TIMEOUT
from utils.log_utils import setup_logger

class GPSReader:
    def __init__(self, port=GPS_PORT, baudrate=GPS_BAUDRATE, timeout=GPS_TIMEOUT, logger=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.lock = threading.Lock()
        self.logger = logger or setup_logger("gps_reader", log_file="gps.log")
        self._connect()

    def _connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        except Exception as e:
            if self.logger:
                self.logger.error(f"No se pudo abrir el puerto {self.port}: {e}")
            self.serial = None

    def read_sentence(self):
        """
        Lee una línea del GPS (formato NMEA). Retorna una cadena cruda o None si hay error.
        """
        if not self.serial or not self.serial.is_open:
            self._connect()
            return None

        try:
            with self.lock:
                line = self.serial.readline().decode('ascii', errors='ignore').strip()
            if line.startswith("$"):
                return line
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al leer desde GPS: {e}")
        return None

    def close(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
