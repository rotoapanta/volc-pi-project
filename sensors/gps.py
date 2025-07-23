# sensors/gps.py

import serial
import threading

class GPSReader:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.lock = threading.Lock()
        self._connect()

    def _connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        except Exception as e:
            print(f"[ERROR] No se pudo abrir el puerto {self.port}: {e}")
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
            print(f"[ERROR] al leer desde GPS: {e}")
        return None

    def close(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
