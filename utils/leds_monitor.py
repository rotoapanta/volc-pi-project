import threading
import time
from utils.leds_utils import LEDManager
from utils.sensors.battery_utils import BatteryMonitor
from sensors.network import network_status_lines

# Si tienes un manager de GPS, puedes importarlo aquí
gps_manager = None
try:
    from managers.gps_manager import GPSManager
    gps_manager = GPSManager(leds=None, logger=None)
except Exception:
    pass

def monitor_leds(leds: LEDManager, interval=1):
    """
    Monitorea periódicamente el estado de batería, red y GPS,
    y actualiza los LEDs correspondientes en caliente.
    """
    def loop():
        battery = BatteryMonitor()
        while True:
            try:
                # Estado de batería
                battery_info = battery.read_all()
                leds.set_battery_status(battery_info["status"])

                # Estado de red
                _, _, wlan_ip, eth_ip = network_status_lines()
                leds.set_network_status(eth_ip, wlan_ip)

                # Estado de GPS (si hay manager disponible)
                if gps_manager is not None:
                    status = getattr(gps_manager, 'gps_status', None)
                    if status:
                        leds.set_gps_status(status)
            except Exception as e:
                # Loguea el error pero no detiene el hilo
                try:
                    from utils.log_utils import setup_logger
                    logger = setup_logger("leds_monitor")
                    logger.error(f"Error en monitor_leds: {e}")
                except Exception:
                    pass
            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t

# Ejemplo de uso:
# leds = LEDManager()
# monitor_leds(leds, interval=1)
