import time
import threading

from config import (
    GPS_PORT,
    GPS_BAUDRATE,
    GPS_TIMEOUT,
    GPS_MIN_SATELLITES,
    GPS_REQUIRED_FIX_QUALITY
)

from sensors.gps import GPSReader
from utils.gps_utils import (
    parse_nmea_sentence,
    extract_coordinates,
    extract_altitude,
    extract_satellite_count,
    extract_utc_time,
    sync_system_clock
)


class GPSManager:
    def __init__(self, leds=None, logger=None):
        self.gps = GPSReader(port=GPS_PORT, baudrate=GPS_BAUDRATE, timeout=GPS_TIMEOUT)
        self.leds = leds
        self.logger = logger

        self.gps_status = "NO_FIX"
        self.has_synced_time = False

        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.satellites = 0
        self._stop_flag = False
        self._thread = None

    def start(self):
        """Inicia el monitoreo continuo del GPS en un hilo."""
        self._stop_flag = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Bucle continuo de lectura y análisis del GPS."""
        last_fix_time = time.time()
        fix_timeout = 3.0  # Segundos sin FIX antes de cambiar a SEARCHING
        while not self._stop_flag:
            sentence = self.gps.read_sentence()
            if not sentence:
                continue

            nmea_msg = parse_nmea_sentence(sentence)
            if not nmea_msg:
                continue

            coords = extract_coordinates(nmea_msg)
            alt = extract_altitude(nmea_msg)
            sats = extract_satellite_count(nmea_msg)
            utc_time = extract_utc_time(nmea_msg)

            lat, lon = coords if coords else (None, None)

            self.latitude = lat
            self.longitude = lon
            self.altitude = alt
            self.satellites = sats

            now = time.time()
            if sats is not None and sats >= GPS_MIN_SATELLITES and lat and lon:
                last_fix_time = now
                if not self.has_synced_time and utc_time:
                    if sync_system_clock(utc_time):
                        if self.logger:
                            self.logger.info(f"⏱️ Hora sincronizada con GPS: {utc_time}")
                        self.has_synced_time = True

                # Siempre mostrar el mensaje de FIX cuando hay posición válida
                if self.logger:
                    self.logger.info(f"📡 FIX GPS con {sats} satélites. Pos: {lat:.5f}, {lon:.5f}, Alt: {alt:.1f} m")
                if self.gps_status != "FIX":
                    self.gps_status = "FIX"
                    if self.leds:
                        self.leds.set_gps_status("FIX")
            else:
                if self.gps_status != "SEARCHING" and (now - last_fix_time) > fix_timeout:
                    if self.logger:
                        self.logger.info("🔍 Buscando FIX GPS...")
                    self.gps_status = "SEARCHING"
                    if self.leds:
                        self.leds.set_gps_status("SEARCHING")

            time.sleep(0.5)

        if self.leds:
            self.leds.set_gps_status("NO_FIX")
        if self.logger:
            self.logger.info("🛰️ GPS detenido.")

    def get_coordinates(self):
        return (self.latitude, self.longitude)

    def get_altitude(self):
        return self.altitude

    def get_satellites(self):
        return self.satellites

    def stop(self):
        self._stop_flag = True
        if self._thread:
            self._thread.join(timeout=1.0)
        self.gps.close()
        if self.logger:
            self.logger.info("🛰️ Hilo GPS detenido.")
