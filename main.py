# main.py — Punto de entrada principal del sistema

from config import STATION_NAME, IDENTIFIER, ACQUISITION_INTERVAL
from station.weather_station import WeatherStation
from diagnostics.startup import startup_diagnostics
from utils.leds_utils import LEDManager
from utils.log_utils import setup_logger
from utils.power_guard import PowerGuard
from managers.gps_manager import GPSManager  # ← IMPORTANTE
from utils.usb_monitor import start_usb_monitor
from sensors.seismic import SeismicSensor
import time

if __name__ == "__main__":
    logger = setup_logger()
    leds = LEDManager()

    startup_diagnostics(leds, logger=logger)
    # Inicia monitoreo dinámico de USB para el LED MEDIA
    start_usb_monitor(leds, logger=logger)

    # Inicia monitoreo continuo de batería
    power_guard = PowerGuard(leds, logger)
    power_guard.start()

    # Inicia monitoreo GPS (en hilo)
    gps_manager = GPSManager(leds=leds, logger=logger)
    gps_manager.start()

    station = WeatherStation(
        station_name=STATION_NAME,
        identifier=IDENTIFIER,
        acquisition_interval=ACQUISITION_INTERVAL,
        leds=leds,
        logger=logger
    )

    # Inicia el sensor sísmico
    from utils.seismic_utils import SeismicDataAccumulator
    from config import SEISMIC_STORAGE_INTERVAL_MINUTES
    seismic_acc = SeismicDataAccumulator(acquisition_interval=SEISMIC_STORAGE_INTERVAL_MINUTES)
    from utils.battery_utils import BatteryMonitor
    battery_monitor = BatteryMonitor()
    import json
    def get_last_gps():
        try:
            with open("last_gps.json", "r") as f:
                data = json.load(f)
                return data.get("lat"), data.get("lon"), data.get("alt")
        except Exception:
            return None, None, None

    def seismic_callback(data):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logger.info(f"[SEISMIC] TIME={timestamp} {data}")
        lat, lon, alt = get_last_gps()
        voltage = battery_monitor.read_all()["voltage"]
        # Solo guardar si hay posición válida de GPS
        if lat is not None and lon is not None and alt is not None:
            seismic_acc.accumulate_and_save(
                data,
                latitud=lat,
                longitud=lon,
                altura=alt,
                voltage=voltage
            )
        else:
            logger.warning("No se guarda dato sísmico: aún no hay fix de GPS.")
    from config import SEISMIC_PORT, SEISMIC_BAUDRATE
    seismic_sensor = SeismicSensor(port=SEISMIC_PORT, baudrate=SEISMIC_BAUDRATE, callback=seismic_callback)
    try:
        seismic_sensor.start()
    except Exception as e:
        logger.warning(f"No se pudo iniciar el sensor sísmico: {e}")

    
    try:
        station.run()
    finally:
        gps_manager.stop()  # ← Asegura cerrar hilo GPS
        seismic_sensor.stop()
