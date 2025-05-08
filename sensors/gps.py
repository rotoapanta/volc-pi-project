import serial
import pynmea2
from config import GPS_PORT, GPS_BAUDRATE, GPS_TIMEOUT

class GPSReader:
    def __init__(self, port=GPS_PORT, baudrate=GPS_BAUDRATE, timeout=GPS_TIMEOUT):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None

    def connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            return True
        except serial.SerialException as e:
            print(f"❌ No se pudo abrir el puerto GPS ({self.port}): {e}")
            return False

    def read_line(self):
        if self.serial and self.serial.in_waiting:
            try:
                return self.serial.readline().decode('ascii', errors='replace').strip()
            except Exception:
                return None
        return None

    def read_sentence(self, expected=("GGA", "RMC")):
        line = self.read_line()
        if not line:
            return None

        try:
            msg = pynmea2.parse(line)
            if msg.sentence_type in expected:
                return msg
        except pynmea2.ParseError:
            pass
        return None

    def close(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
