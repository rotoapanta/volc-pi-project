import serial
import threading

class SeismicSensor:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, callback=None):
        self.port = port
        self.baudrate = baudrate
        self.callback = callback  # función a llamar con cada dato recibido
        self._stop_event = threading.Event()
        self._thread = None
        self.ser = None

    def start(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
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
                print(f"[WARN] Error leyendo sensor sísmico: {e}")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        if self.ser:
            self.ser.close()
