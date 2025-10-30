# sensors/gps.py

import threading
from config import GPS_PORT, GPS_BAUDRATE, GPS_TIMEOUT
from utils.log_utils import setup_logger
from sensors.serial_port import RobustSerial

class GPSReader:
    def __init__(self, port=GPS_PORT, baudrate=GPS_BAUDRATE, timeout=GPS_TIMEOUT, logger=None,
                 max_open_failures=5, open_cooldown_seconds=30, read_delay=0.2, backoff_factor=2.0, max_backoff=2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.lock = threading.Lock()
        self.logger = logger or setup_logger("gps_reader", log_file="gps.log")
        self.serial = RobustSerial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            logger=self.logger,
            max_open_failures=max_open_failures,
            open_cooldown_seconds=open_cooldown_seconds,
            read_delay=read_delay,
            backoff_factor=backoff_factor,
            max_backoff=max_backoff,
        )

    def read_sentence(self):
        """
        Lee una línea del GPS (formato NMEA). Retorna una cadena cruda o None si hay error.
        """
        try:
            with self.lock:
                data = self.serial.readline()
            if not data:
                return None
            line = data.decode('ascii', errors='ignore').strip()
            if line.startswith("$"):
                return line
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error al leer desde GPS: {e}")
        return None

    def close(self):
        self.serial.close()
