import threading
import time
import subprocess
import logging

from utils.battery_utils import BatteryMonitor

# Parámetros de apagado seguro
BATTERY_CHECK_INTERVAL = 60  # en segundos
MAX_CRITICAL_CYCLES = 3      # número de chequeos consecutivos en estado CRÍTICA
CRITICAL_LOG_TAG = "🟥"

class PowerGuard(threading.Thread):
    def __init__(self, leds=None, logger=None):
        super().__init__(daemon=True)
        self.leds = leds
        self.logger = logger or logging.getLogger("power_guard")
        self.battery = BatteryMonitor()
        self.critical_count = 0

    def run(self):
        while True:
            try:
                info = self.battery.read_all()
                voltage = info["voltage"]
                status = info["status"]

                if status == "CRÍTICA":
                    self.critical_count += 1
                    self.logger.warning(f"{CRITICAL_LOG_TAG} Batería crítica: {voltage:.2f} V - ciclo {self.critical_count}/{MAX_CRITICAL_CYCLES}")
                    if self.critical_count >= MAX_CRITICAL_CYCLES:
                        self.logger.critical("[BATTERY] ⚠️ Apagando sistema por batería crítica")
                        if self.leds:
                            self.leds.set("ERROR", True)
                        time.sleep(2)  # pequeña espera para ver el LED
                        subprocess.call(['sudo', 'shutdown', '-h', 'now'])
                        break
                else:
                    self.critical_count = 0
                    msg = f"[BATTERY] 🔋 Stable: {voltage:.2f} V ({status})"
                    self.logger.info(msg)

                # LED indicador si se desea:
                if self.leds:
                    self.leds.set_battery_status(status)

            except Exception as e:
                self.logger.error(f"Error en PowerGuard: {e}")

            time.sleep(BATTERY_CHECK_INTERVAL)
