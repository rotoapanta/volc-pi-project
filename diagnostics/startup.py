# diagnostics/startup.py

import os
import shutil
import lgpio

from config import RAIN_SENSOR_PIN
from utils.storage_utils import find_mounted_usb, has_enough_space
from sensors.network import is_connected, network_status_lines
from utils.battery_utils import BatteryMonitor

MIN_FREE_MB = 50

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

    print("\n==================== INICIALIZACIÓN DEL SISTEMA ====================")

    # 1. Verificación del sensor de lluvia
    try:
        chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(chip, RAIN_SENSOR_PIN)
        print(f"[ OK ] Sensor de lluvia conectado en GPIO {RAIN_SENSOR_PIN}")
        lgpio.gpiochip_close(chip)
    except Exception as e:
        print(f"[FAIL] Error al configurar el sensor de lluvia: {e}")
        logger.error(f"Sensor de lluvia no disponible: {e}")
        leds.set("ERROR", True)

    # 2. Verificación de la memoria USB
    usb = find_mounted_usb()
    if usb:
        try:
            free_mb = shutil.disk_usage(usb).free // (1024 ** 2)
            print(f"[ OK ] Memoria USB detectada en {usb} - Espacio libre: {free_mb} MB")
            logger.info(f"USB detectada en {usb} - Espacio libre: {free_mb} MB")
            if free_mb < MIN_FREE_MB:
                print(f"[WARN] Espacio bajo en USB (<{MIN_FREE_MB} MB)")
                logger.warning("Espacio bajo en USB")
                leds.set("ERROR", True)
        except Exception as e:
            print(f"[FAIL] No se pudo acceder al USB montado: {e}")
            logger.error(f"No se pudo verificar espacio en USB: {e}")
            leds.set("ERROR", True)
    else:
        print("[WARN] No se detectó memoria USB. Se usará almacenamiento interno.")
        logger.warning("No se detectó USB. Usando almacenamiento interno.")
        leds.set("MEDIA", True)

    # 3. Verificación de espacio local
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    try:
        local_free_mb = shutil.disk_usage(local_path).free // (1024 ** 2)
        print(f"[ OK ] Espacio en respaldo local: {local_free_mb} MB")
        logger.info(f"Espacio en respaldo local: {local_free_mb} MB")
    except Exception as e:
        print(f"[FAIL] No se pudo verificar espacio local: {e}")
        logger.error(f"No se pudo verificar espacio local: {e}")
        leds.set("ERROR", True)

    # 4. Estado del GPS (placeholder)
    print("[....] GPS: módulo no implementado aún")
    logger.debug("Estado GPS: no implementado")

    # 5. Estado de LoRa (placeholder)
    print("[....] LoRa: módulo no implementado aún")
    logger.debug("Estado LoRa: no implementado")

    # 6. Estado de red
    for line in network_status_lines():
        print(line)
        if "WARN" in line:
            logger.warning(line.replace("[WARN]", "").strip())
        elif "OK" in line:
            logger.info(line.replace("[ OK ]", "").strip())

    # 7. LED de red
    if is_connected():
        print("[INFO] Red detectada, encendiendo LED NET")
        leds.set("NET", True)
    else:
        print("[INFO] Sin red, LED NET apagado")
        leds.set("NET", False)

    # 8. Estado de la batería
    battery = BatteryMonitor()
    battery_info = battery.read_all()
    # battery.close()  # No cerrar el bus I2C aquí para evitar conflictos

    # Control visual con LED de batería
    leds.set_battery_status(battery_info["status"])

    # Mensaje en consola
    if battery_info['voltage'] is not None:
        print(f"[ OK ] Voltaje de batería inicial: {battery_info['voltage']:.2f} V ({battery_info['status']})")
    else:
        print(f"[WARN] Voltaje de batería inicial: ERROR ({battery_info['status']})")

    # Log según estado
    if battery_info["status"] == "BAJA":
        logger.warning("⚠️ Nivel de batería bajo")
    elif battery_info["voltage"] is not None:
        logger.info(f"🔋 Voltaje de batería inicial: {battery_info['voltage']:.2f} V - {battery_info['status']}")
    else:
        logger.error(f"🔋 Error al leer voltaje de batería inicial - Estado: {battery_info['status']}")

    print("===================================================================\n")
