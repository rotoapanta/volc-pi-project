from utils.log_utils import setup_logger
import os
import threading
from utils.storage.block_storage import BlockStorage
from utils.storage.storage_utils import find_mounted_usb
from utils.leds_utils import LEDManager
from diagnostics.startup import startup_diagnostics
from config import (
    STATION_NAME, IDENTIFIER, SEISMIC_STATION_TYPE, SEISMIC_MODEL, SEISMIC_SERIAL_NUMBER,
    SEISMIC_PORT, SEISMIC_BAUDRATE, PLUVI_STATION_TYPE, PLUVI_MODEL, PLUVI_SERIAL_NUMBER,
    BLOCK_TYPE, SENSORS
)
from managers.seismic_manager import SeismicManager
from managers.rain_manager import RainManager
from config import INTERNAL_BACKUP_DIR

# ------------------- Inicialización de sistema y recursos -------------------

# LEDs y diagnóstico
leds = LEDManager()
leds.heartbeat()
startup_diagnostics(leds)

# Logger centralizado
logger = setup_logger("main")

# Selección dinámica de ruta de almacenamiento
usb_path = find_mounted_usb()
if usb_path:
    output_dir = os.path.join(usb_path, "DTA")
    logger.info(f"Almacenamiento USB detectado: {output_dir}")
else:
    output_dir = INTERNAL_BACKUP_DIR
    logger.warning(f"No se detectó USB, usando almacenamiento interno: {output_dir}")

# ------------------- Configuración de sensores y almacenamiento -------------------

# Intervalos
seismic_sensor = next((s for s in SENSORS if s["name"] == "seismic"), None)
interval_minutes = seismic_sensor["interval_minutes"] if seismic_sensor else 1
rain_sensor = next((s for s in SENSORS if s["name"] == "rain"), None)
pluvi_interval_minutes = rain_sensor["interval_minutes"] if rain_sensor else 1

# Almacenamiento
from utils.extractors.data_extractors import extract_seismic
seismic_storage = BlockStorage(
    station_name=STATION_NAME,
    identifier=IDENTIFIER,
    model=SEISMIC_MODEL,
    serial_number=SEISMIC_SERIAL_NUMBER,
    logger=logger,
    output_dir=output_dir,
    block_type=BLOCK_TYPE,
    tipo=SEISMIC_STATION_TYPE,
    interval_minutes=interval_minutes,
    extractor_func=extract_seismic
)
from utils.extractors.data_extractors import extract_rain
pluvi_storage = BlockStorage(
    station_name=STATION_NAME,
    identifier=IDENTIFIER,
    model=PLUVI_MODEL,
    serial_number=PLUVI_SERIAL_NUMBER,
    logger=logger,
    output_dir=output_dir,
    block_type=BLOCK_TYPE,
    tipo=PLUVI_STATION_TYPE,
    interval_minutes=pluvi_interval_minutes,
    extractor_func=extract_rain
)

# ------------------- Inicialización de managers -------------------

# SeismicManager
seismic_config = {
    "port": SEISMIC_PORT,
    "baudrate": SEISMIC_BAUDRATE,
    "interval": interval_minutes * 60  # segundos
}
seismic_manager = SeismicManager(seismic_config, logger, seismic_storage)

# RainManager
rain_config = {
    "interval": pluvi_interval_minutes * 60  # segundos
}
rain_manager = RainManager(rain_config, logger, pluvi_storage)

# ------------------- Lanzamiento de hilos de sensores -------------------

threads = []
threads.append(threading.Thread(target=seismic_manager.run, daemon=True))
threads.append(threading.Thread(target=rain_manager.run, daemon=True))
for t in threads:
    t.start()

# ------------------- Monitor de USB hotplug y migración de datos -------------------
import time
from utils.storage.migrate_to_usb import migrate_internal_to_usb

def usb_hotplug_monitor(seismic_storage, pluvi_storage, logger, internal_dir, leds, check_interval=5):
    usb_connected = False
    last_usb_path = None
    while True:
        usb_path = find_mounted_usb()
        if usb_path and not usb_connected:
            # USB conectada
            output_dir = os.path.join(usb_path, "DTA")
            logger.info(f"Memoria USB detectada: {output_dir}. Cambiando almacenamiento y migrando datos...")
            seismic_storage.set_output_dir(output_dir)
            pluvi_storage.set_output_dir(output_dir)
            # Migrar archivos pendientes
            files_migrated = migrate_internal_to_usb(internal_dir, output_dir, logger)
            logger.info(f"Migración completada. Archivos migrados: {files_migrated}")
            # Apagar LED MEDIA (USB presente)
            if leds:
                leds.set("MEDIA", False)
            usb_connected = True
            last_usb_path = usb_path
        elif not usb_path and usb_connected:
            # USB desconectada
            logger.warning("[HOTPLUG] Memoria USB desconectada. Volviendo a almacenamiento interno.")
            seismic_storage.set_output_dir(internal_dir)
            pluvi_storage.set_output_dir(internal_dir)
            # Encender LED MEDIA (USB ausente)
            if leds:
                leds.set("MEDIA", True)
            usb_connected = False
            last_usb_path = None
        time.sleep(check_interval)

# Lanzar el monitor en un hilo aparte
t_monitor = threading.Thread(
    target=usb_hotplug_monitor,
    args=(seismic_storage, pluvi_storage, logger, INTERNAL_BACKUP_DIR, leds),
    daemon=True
)
t_monitor.start()

# ------------------- Bucle principal (keep-alive y limpieza) -------------------

try:
    while True:
        time.sleep(1)  # El sistema sigue corriendo, managers activos en hilos
except KeyboardInterrupt:
    logger.info("Terminando y guardando datos pendientes...")
    # Aquí podrías agregar métodos de parada para los managers si lo deseas
    leds.cleanup()
