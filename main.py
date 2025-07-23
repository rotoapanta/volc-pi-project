# main.py — Punto de entrada principal del sistema

from config import STATION_NAME, IDENTIFIER, ACQUISITION_INTERVAL
from station.weather_station import WeatherStation
from diagnostics.startup import startup_diagnostics
from utils.leds_utils import LEDManager
from utils.log_utils import setup_logger
from utils.power_guard import PowerGuard
from managers.gps_manager import GPSManager  # ← IMPORTANTE
from utils.usb_monitor import start_usb_monitor

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

    try:
        station.run()
    finally:
        gps_manager.stop()  # ← Asegura cerrar hilo GPS
