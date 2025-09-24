# diagnostics/startup.py

import os
import shutil
import lgpio

from utils.logs.print_utils import print_colored

from config import RAIN_SENSOR_PIN, MIN_FREE_MB
from utils.storage.storage_utils import find_mounted_usb, has_enough_space
from sensors.network import is_connected, network_status_lines
from utils.sensors.battery_utils import BatteryMonitor


def startup_diagnostics(leds, logger=None):
    """
    Ejecuta diagnósticos iniciales del sistema:
    - Verifica sensor de lluvia
    - Verifica USB y espacio local
    - Verifica red (Wi-Fi, LAN e Internet)
    - Verifica voltaje de batería
    """
    if logger is None:
        from utils.log_utils import setup_logger
        logger = setup_logger("startup")
    # Inicializa los loggers dedicados para GPS y sincronización de hora
    from utils.log_utils import setup_logger as setup_sync_logger
    gps_logger = setup_sync_logger("gps", log_file="gps.log")
    sync_logger = setup_sync_logger("sync", log_file="sync.log")

    logger.info("==================== INICIALIZACIÓN DEL SISTEMA ====================")
    # Mensaje de estación activa
    try:
        from config import STATION_NAME, RAIN_INTERVAL_MINUTES
        msg = f"Estación activa: {STATION_NAME} - Intervalo de adquisición: {RAIN_INTERVAL_MINUTES} min"
        logger.info(msg)
    except Exception as e:
        logger.warning(f"No se pudo mostrar mensaje de estación activa: {e}")

    # 1. Verificación del sensor de lluvia
    try:
        chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(chip, RAIN_SENSOR_PIN)
        logger.info(f"Sensor de lluvia configurado | GPIO: {RAIN_SENSOR_PIN}")
        lgpio.gpiochip_close(chip)
    except Exception as e:
        logger.error(f"Sensor de lluvia: error al configurar ({e})")
        leds.set("ERROR", True)

    # 2. Verificación de la memoria USB
    usb = find_mounted_usb()
    if usb:
        try:
            free_mb = shutil.disk_usage(usb).free // (1024 ** 2)
            logger.info(f"Memoria USB detectada | Ruta: {usb} | Espacio libre: {free_mb} MB")
            if free_mb < MIN_FREE_MB:
                logger.warning(f"Memoria USB: espacio bajo (<{MIN_FREE_MB} MB)")
                leds.set("ERROR", True)
        except Exception as e:
            logger.error(f"Memoria USB: error al acceder ({e})")
            leds.set("ERROR", True)
    else:
        local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        logger.warning(f"Memoria USB no detectada | Usando almacenamiento interno: {local_path}")
        leds.set("MEDIA", True)

    # 3. Verificación de espacio local
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    try:
        local_free_mb = shutil.disk_usage(local_path).free // (1024 ** 2)
        logger.info(f"Espacio local configurado | Ruta: {local_path} | Espacio libre: {local_free_mb} MB")
    except Exception as e:
        logger.error(f"Espacio local: error al verificar ({e})")
        leds.set("ERROR", True)

    # 4. Estado del GPS
    try:
        from config import GPS_PORT, GPS_BAUDRATE, GPS_SYNC_INTERVAL_SECONDS
        from managers.gps_manager import GPSManager
        gps_manager = GPSManager(leds=leds, logger=gps_logger, sync_logger=sync_logger, sync_interval_seconds=GPS_SYNC_INTERVAL_SECONDS)
        gps_manager.start()
        gps_port_short = os.path.basename(GPS_PORT)
        logger.info(
            f"GPS configurado | Puerto: {gps_port_short} | Baudrate: {GPS_BAUDRATE} | "
            f"Sync interval: {GPS_SYNC_INTERVAL_SECONDS} s"
        )
    except Exception as e:
        logger.debug(f"GPS: módulo no implementado o error ({e})")

    # 8. Estado de la batería
    battery = BatteryMonitor()
    battery_info = battery.read_all()
    # battery.close()  # No cerrar el bus I2C aquí para evitar conflictos

    # Control visual con LED de batería
    leds.set_battery_status(battery_info["status"])


    # 5. Estado del módulo sísmico
    try:
        from config import SEISMIC_PORT, SEISMIC_BAUDRATE, SEISMIC_INTERVAL_MINUTES, SEISMIC_MODEL, SEISMIC_SERIAL_NUMBER, SEISMIC_STATION_TYPE
        from managers.seismic_manager import SeismicManager
        seismic_config = {
            "port": SEISMIC_PORT,
            "baudrate": SEISMIC_BAUDRATE,
            "interval": SEISMIC_INTERVAL_MINUTES * 60  # en segundos
        }
        seismic_manager = SeismicManager(seismic_config, logger=logger)
        seismic_port_short = os.path.basename(SEISMIC_PORT)
        logger.info(
            f"Módulo sísmico configurado | "
            f"Puerto: {seismic_port_short} | Baudrate: {SEISMIC_BAUDRATE} | "
            f"Intervalo: {SEISMIC_INTERVAL_MINUTES} min"
        )
        # Si quieres arrancar el proceso/hilo, descomenta la siguiente línea:
        # seismic_manager.start()  # Solo si SeismicManager implementa start/hilo
    except Exception as e:
        logger.warning(f"Módulo sísmico: error al inicializar ({e})")

    # 6. Estado de LoRa (placeholder)
    logger.info("LoRa: módulo no implementado aún")
    logger.debug("Estado LoRa: no implementado")

    # 7. Estado de red
    lines, conectado, wlan_ip, eth_ip = network_status_lines()
    for nivel, mensaje in lines:
        getattr(logger, nivel)(mensaje)
    leds.set_network_status(eth_ip, wlan_ip)


    # 10. Mensaje en log
    if battery_info['voltage'] is not None:
        # Solo mostrar el mensaje con emoji para evitar duplicidad
        logger.info(f"Voltaje de batería inicial: {battery_info['voltage']:.2f} V | {battery_info['status']}")
    else:
        logger.warning(f"Voltaje de batería inicial: ERROR ({battery_info['status']})")

    # 11. Log según estado
    if battery_info["status"] == "BAJA":
        logger.warning("Nivel de batería bajo")
    elif battery_info["voltage"] is not None:
        from datetime import datetime
    else:
        logger.error(f"Error al leer voltaje de batería inicial - Estado: {battery_info['status']}")
    logger.info("===================================================================")
