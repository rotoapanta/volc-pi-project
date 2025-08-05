import serial
import threading
import glob
import os
from utils.sensors.seismic_utils import parse_seismic_message
from config import STATION_NAME, IDENTIFIER, SEISMIC_MODEL, SEISMIC_SERIAL_NUMBER

from datetime import datetime

class SeismicSensor:
    def __init__(self, port=None, baudrate=9600, callback=None, interval_minutes=1):
        # Si no se especifica puerto, busca automáticamente en /dev/serial/by-id/
        if port is None:
            by_id = glob.glob('/dev/serial/by-id/*')
            if by_id:
                self.port = by_id[0]
                print(f"[INFO] Usando puerto sísmico: {self.port}")
            else:
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
        # Instancia el almacenamiento genérico para sísmico
        # Eliminado: el almacenamiento ahora lo gestiona BlockStorage desde el manager

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

    def acquire(self):
        """Lee una línea del sensor sísmico y la devuelve como string."""
        if self.ser is None:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        try:
            line = self.ser.readline().decode(errors='ignore').strip()
            if line:
                print(f"[SEISMIC] Dato crudo recibido: {line}")
            else:
                print("[SEISMIC] No se recibió dato sísmico")
            return line
        except Exception as e:
            print(f"[WARN] Error leyendo sensor sísmico (acquire): {e}")
            return None

    def process(self, raw, fecha, tiempo, latitud=None, longitud=None, altura=None, voltage=None):
        """Procesa la línea cruda del sensor sísmico usando la función centralizada."""
        return parse_seismic_message(raw, fecha, tiempo, latitud=latitud, longitud=longitud, altura=altura, voltage=voltage)

    # Eliminado: el guardado ahora lo gestiona BlockStorage desde el manager
