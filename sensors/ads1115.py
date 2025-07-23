# sensors/ads1115.py

import smbus2
import time

# Constantes del divisor resistivo (ajusta si cambian los valores)
R1 = 100_000  # 100kΩ
R2 = 15_000   # 15kΩ

# Dirección I2C y configuración
ADS1115_ADDRESS = 0x48
I2C_BUS = 1

# Registros
ADS1115_POINTER_CONVERT = 0x00
ADS1115_POINTER_CONFIG = 0x01

# Configuración: AIN0, PGA ±4.096V, single-shot, 128SPS
ADS1115_CONFIG = 0xC283
ADC_RANGE = 4.096  # Volts
ADC_RESOLUTION = 32768  # 16 bits (signed)

class ADS1115Reader:
    def __init__(self, bus=I2C_BUS, address=ADS1115_ADDRESS):
        self.bus = smbus2.SMBus(bus)
        self.address = address

    def read_raw(self, channel=0):
        """Lee el valor crudo del canal especificado."""
        if channel < 0 or channel > 3:
            raise ValueError("Canal inválido: debe ser 0–3")
        
        config = ADS1115_CONFIG | (channel << 12)
        config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
        self.bus.write_i2c_block_data(self.address, ADS1115_POINTER_CONFIG, config_bytes)
        time.sleep(0.02)

        result = self.bus.read_i2c_block_data(self.address, ADS1115_POINTER_CONVERT, 2)
        raw = (result[0] << 8) | result[1]

        if raw > 0x7FFF:
            raw -= 0x10000

        return raw

    def read_voltage(self, channel=0):
        """Convierte la lectura cruda en voltios."""
        raw = self.read_raw(channel)
        return (raw * ADC_RANGE) / ADC_RESOLUTION

    def read_battery_voltage(self, channel=0):
        """
        Devuelve el voltaje real de batería considerando el divisor resistivo.
        NO aplica calibración adicional (eso va en battery_utils).
        """
        vout = self.read_voltage(channel)
        vin = vout * (R1 + R2) / R2
        return vin

    def close(self):
        """Cierra el bus I2C correctamente."""
        self.bus.close()
