import threading
import time
from sensors.network import network_status_lines

def start_network_monitor(leds, logger, interval=5):
    """
    Inicia un hilo que monitorea el estado de la red (LAN y Wi-Fi) y muestra mensajes
    cuando hay cambios de estado. También actualiza los LEDs de red.
    """
    def monitor():
        last_eth_ip = None
        last_wlan_ip = None
        last_connected = None
        while True:
            lines, connected, wlan_ip, eth_ip = network_status_lines()
            # Detectar cambios en la LAN
            if eth_ip != last_eth_ip:
                if eth_ip:
                    logger.info(f"LAN conectada | eth0 - IP: {eth_ip}")
                else:
                    logger.warning("LAN no conectada")
                last_eth_ip = eth_ip
            # Detectar cambios en la Wi-Fi
            if wlan_ip != last_wlan_ip:
                if wlan_ip:
                    logger.info(f"Wi-Fi conectada | wlan0 - IP: {wlan_ip}")
                else:
                    logger.warning("Wi-Fi no conectada")
                last_wlan_ip = wlan_ip
            # Detectar cambios en el acceso a Internet
            if connected != last_connected:
                if connected:
                    logger.info("Acceso a Internet disponible")
                else:
                    logger.warning("Sin acceso a Internet")
                last_connected = connected
            # Actualizar LEDs de red
            leds.set_network_status(eth_ip, wlan_ip)
            time.sleep(interval)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
