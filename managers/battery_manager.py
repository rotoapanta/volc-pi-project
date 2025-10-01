from utils.sensors.battery_utils import BatteryMonitor

def get_last_battery_voltage():
    """Lee el voltaje real de la batería usando BatteryMonitor y ADS1115."""
    monitor = BatteryMonitor()
    voltage = monitor.read_voltage()
    monitor.close()
    return voltage
