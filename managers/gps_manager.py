import time
import threading
import json
import os

from config import (
    GPS_PORT,
    GPS_BAUDRATE,
    GPS_TIMEOUT,
    GPS_MIN_SATELLITES,
    GPS_REQUIRED_FIX_QUALITY
)

from sensors.gps import GPSReader
from utils.sensors.gps_utils import (
    parse_nmea_sentence,
    extract_coordinates,
    extract_altitude,
    extract_satellite_count,
    extract_utc_time,
    sync_system_clock
)

class GPSManager:
    """
    Gestor para el monitoreo y manejo del GPS en un hilo separado.
    Permite obtener coordenadas, altitud y número de satélites, y sincronizar el reloj del sistema.

    Manager for monitoring and handling GPS in a separate thread.
    Allows obtaining coordinates, altitude, satellite count, and synchronizing the system clock.
    """
    def __init__(self, leds=None, logger=None, sync_logger=None, sync_interval_seconds=3600):
        """
        Inicializa el gestor de GPS con soporte opcional para LEDs y dos loggers (general y de sincronización).
        Permite configurar el intervalo de sincronización del reloj del sistema (por defecto 1 hora).

        Initializes the GPS manager with optional support for LEDs and two loggers (general and sync).
        Allows configuring the system clock sync interval (default 1 hour).
        """
        self.gps = GPSReader(port=GPS_PORT, baudrate=GPS_BAUDRATE, timeout=GPS_TIMEOUT, logger=logger)
        self.leds = leds
        self.logger = logger
        self.sync_logger = sync_logger

        self.gps_status = "NO_FIX"
        self.has_synced_time = False
        self.sync_interval_seconds = sync_interval_seconds
        self.last_sync_time = 0

        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.satellites = 0
        self._stop_flag = False
        self._thread = None

    def start(self):
        """
        Inicia el monitoreo continuo del GPS en un hilo.

        Starts continuous GPS monitoring in a separate thread.
        """
        self._stop_flag = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """
        Bucle continuo de lectura y análisis del GPS.

        Continuous loop for reading and analyzing GPS data.
        """
        last_fix_time = time.time()
        from config import GPS_FIX_TIMEOUT, GPS_LOOP_SLEEP, GPS_RESYNC_ON_FIX_LOSS, GPS_RESYNC_MIN_LOSS_SECONDS
        fix_timeout = GPS_FIX_TIMEOUT
        last_gps = {"lat": None, "lon": None, "alt": None}
        last_status = None
        last_lost_fix_time = None
        self.has_synced_time = False
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

            # (No registrar datos crudos en el log, solo eventos clave)
            # if self.logger:
            #     if lat is not None and lon is not None and (lat, lon, alt) != (last_gps["lat"], last_gps["lon"], last_gps["alt"]):
            #         msg = f"[GPS] Dato crudo recibido: lat: {lat} lon: {lon} alt: {alt}"
            #         self.logger.info(msg)
            #         last_gps = {"lat": lat, "lon": lon, "alt": alt}

            self.latitude = lat
            self.longitude = lon
            self.altitude = alt
            self.satellites = sats

            now = time.time()
            if sats is not None and sats >= GPS_MIN_SATELLITES and lat and lon:
                last_fix_time = now
                # Sincronizar al arranque o si se recupera FIX tras una pérdida prolongada
                # Sync at startup or if FIX is recovered after a long loss
                do_sync = False
                if not self.has_synced_time and utc_time:
                    do_sync = True
                elif GPS_RESYNC_ON_FIX_LOSS and last_lost_fix_time is not None and (now - last_lost_fix_time) >= GPS_RESYNC_MIN_LOSS_SECONDS and utc_time:
                    do_sync = True
                # Solo sincronizar si ha pasado el intervalo configurado
                if do_sync and (now - self.last_sync_time) >= self.sync_interval_seconds:
                    if sync_system_clock(utc_time, logger=self.sync_logger):
                        self.has_synced_time = True
                        self.last_sync_time = now
                    last_lost_fix_time = None

                # Guardar la última posición GPS válida en un archivo / Save last valid GPS position
                try:
                    with open("last_gps.json", "w") as f:
                        json.dump({"lat": lat, "lon": lon, "alt": alt}, f)
                    if self.logger:
                        self.logger.info(f"last_gps.json actualizado | lat={lat} lon={lon} alt={alt}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error guardando last_gps.json: {e}")

                # Siempre mostrar el mensaje de FIX cuando hay posición válida
                # Always show FIX message when position is valid
                if self.logger:
                    msg = f"Fix: Sats: {sats} | Pos: {lat:.5f} | {lon:.5f} | Alt: {alt:.1f} m"
                    self.logger.info(msg)
                if self.gps_status != "FIX":
                    self.gps_status = "FIX"
                    if self.leds:
                        self.leds.set_gps_status("FIX")
            else:
                # Si se pierde FIX, marca el tiempo de pérdida / If FIX is lost, mark loss time
                if self.gps_status == "FIX":
                    last_lost_fix_time = now
                    self.has_synced_time = False
                if self.gps_status != "SEARCHING" and (now - last_fix_time) > fix_timeout:
                    if last_status != "SEARCHING":
                        if self.logger:
                            msg = "Searching fox Fix..."
                            self.logger.info(msg)
                        last_status = "SEARCHING"
                    self.gps_status = "SEARCHING"
                    if self.leds:
                        self.leds.set_gps_status("SEARCHING")

            time.sleep(GPS_LOOP_SLEEP)

        if self.leds:
            self.leds.set_gps_status("[GPS] NO_FIX")
        if self.logger:
            msg = "[GPS] STOPPED."
            self.logger.info(msg)

    def get_coordinates(self):
        """
        Devuelve una tupla (latitud, longitud) actual.

        Returns a tuple (latitude, longitude) of the current position.
        """
        return (self.latitude, self.longitude)

    def get_altitude(self):
        """
        Devuelve la altitud actual.

        Returns the current altitude.
        """
        return self.altitude

    def get_satellites(self):
        """
        Devuelve el número de satélites visibles actualmente.

        Returns the current number of visible satellites.
        """
        return self.satellites

    def stop(self):
        """
        Detiene el hilo de monitoreo del GPS y cierra el recurso.

        Stops the GPS monitoring thread and closes the resource.
        """
        self._stop_flag = True
        if self._thread:
            self._thread.join(timeout=1.0)
        self.gps.close()
        if self.logger:
            msg = "Thread Stopped."
            self.logger.info(msg)

def get_last_gps_data():
    """
    Lee el último dato de GPS guardado en last_gps.json.

    Reads the last GPS data saved in last_gps.json.
    """
    path = os.path.join(os.path.dirname(__file__), '..', 'last_gps.json')
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return data
    except Exception:
        return {"lat": None, "lon": None, "alt": None}
