import time
import threading
from utils.storage_utils import find_mounted_usb

def monitor_usb(leds, interval=2, logger=None):
    """
    Monitorea la presencia de memoria USB y enciende/apaga el LED MEDIA en tiempo real.
    Además, registra un mensaje cuando se conecta o desconecta la memoria USB.
    """
    usb_present = find_mounted_usb() is not None
    leds.set("MEDIA", not usb_present)
    while True:
        time.sleep(interval)
        new_usb_present = find_mounted_usb() is not None
        if new_usb_present != usb_present:
            leds.set("MEDIA", not new_usb_present)
            if logger:
                if new_usb_present:
                    logger.info("Memoria USB conectada. Cambiando a almacenamiento externo.")
                else:
                    logger.warning("Memoria USB desconectada. Cambiando a almacenamiento interno.")
            else:
                if new_usb_present:
                    print("[INFO] Memoria USB conectada: LED MEDIA apagado")
                else:
                    print("[INFO] Memoria USB desconectada: LED MEDIA encendido")
            usb_present = new_usb_present

def start_usb_monitor(leds, interval=2, logger=None):
    t = threading.Thread(target=monitor_usb, args=(leds, interval, logger), daemon=True)
    t.start()
    return t
