import time
from sensors.ads1115 import ADS1115Reader
from config import (
    BATTERY_ADC_CHANNEL,
    ADS1115_ADDRESS,
    BATTERY_CALIBRATION_SLOPE,
    BATTERY_CALIBRATION_OFFSET,
    BATTERY_LOW_VOLTAGE,
    BATTERY_CRITICAL_VOLTAGE
)

class BatteryMonitor:
    def __init__(self, bus=1):
        self.adc = ADS1115Reader(bus=bus, address=ADS1115_ADDRESS)
        self.channel = BATTERY_ADC_CHANNEL
        self.slope = BATTERY_CALIBRATION_SLOPE
        self.offset = BATTERY_CALIBRATION_OFFSET
        self.low_threshold = BATTERY_LOW_VOLTAGE
        self.critical_threshold = BATTERY_CRITICAL_VOLTAGE

    def read_voltage(self):
        """
        Lee el voltaje de la batería y aplica factor de calibración.
        Si ocurre un error I2C, retorna None y registra el error.
        """
        try:
            raw_voltage = self.adc.read_battery_voltage(channel=self.channel)
            calibrated = raw_voltage * self.slope + self.offset
            return round(calibrated, 2)
        except Exception as e:
            from utils.print_utils import print_colored
            print_colored(f"[ERROR] Error al leer voltaje de batería (I2C): {e}")
            return None

    def get_status(self, voltage):
        """
        Devuelve el estado de la batería según el voltaje.
        """
        if voltage >= self.low_threshold:
            return "NORMAL"
        elif voltage >= self.critical_threshold:
            return "BAJA"
        else:
            return "CRÍTICA"

    def read_all(self):
        """
        Devuelve un diccionario con voltaje y estado de batería.
        Si ocurre un error, retorna estado 'ERROR'.
        """
        voltage = self.read_voltage()
        if voltage is None:
            return {
                "voltage": None,
                "status": "ERROR"
            }
        status = self.get_status(voltage)
        return {
            "voltage": voltage,
            "status": status
        }

    def close(self):
        """
        Cierra el bus I2C del ADC.
        """
        self.adc.close()
