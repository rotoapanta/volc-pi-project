# main.py — Punto de entrada principal del sistema

from config import STATION_NAME, IDENTIFIER, ACQUISITION_INTERVAL
from station.weather_station import WeatherStation
from diagnostics.startup import startup_diagnostics
from utils.leds import LEDManager
from utils.log_utils import setup_logger
from utils.power_guard import PowerGuard

if __name__ == "__main__":
    # Configura el logger principal
    logger = setup_logger()

    # Inicializa el controlador de LEDs
    leds = LEDManager()

    # Ejecuta diagnóstico inicial del sistema
    startup_diagnostics(leds, logger=logger)

    # Inicia el monitoreo de batería en segundo plano
    power_guard = PowerGuard(leds, logger)
    power_guard.start()

    # Inicializa y ejecuta la estación meteorológica
    station = WeatherStation(
        station_name=STATION_NAME,
        identifier=IDENTIFIER,
        acquisition_interval=ACQUISITION_INTERVAL,
        leds=leds,
        logger=logger
    )
    station.run()
