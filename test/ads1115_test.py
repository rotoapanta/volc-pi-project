# ads1115_test.py

import smbus2
import time
from config import BATTERY_CALIBRATION_FACTOR  # <- Importar el factor

# Configuración del ADS1115
I2C_BUS = 1
ADS1115_ADDRESS = 0x4B  # Dirección del ADS1115 (asumida con ADDR a GND)
ADS1115_POINTER_CONVERT = 0x00
ADS1115_POINTER_CONFIG = 0x01

# Config: AIN0, PGA ±4.096V, single-shot, 128SPS
ADS1115_CONFIG = 0xC283
ADC_RANGE = 4.096
ADC_RESOLUTION = 32768

# Divisor resistivo
R1 = 100_000  # 100k ohm
R2 = 15_000   # 15k ohm

def read_voltage(bus, address, channel=0):
    """Lee el voltaje del canal AINx (single-ended)."""
    config = ADS1115_CONFIG | (channel << 12)
    config_bytes = [(config >> 8) & 0xFF, config & 0xFF]

    bus.write_i2c_block_data(address, ADS1115_POINTER_CONFIG, config_bytes)
    time.sleep(0.02)  # Tiempo de conversión para 128SPS

    result = bus.read_i2c_block_data(address, ADS1115_POINTER_CONVERT, 2)
    raw_adc = (result[0] << 8) | result[1]

    if raw_adc > 0x7FFF:
        raw_adc -= 0x10000

    return (raw_adc * ADC_RANGE) / ADC_RESOLUTION

def main():
    bus = smbus2.SMBus(I2C_BUS)
    try:
        while True:
            vout = read_voltage(bus, ADS1115_ADDRESS, channel=0)
            vin = vout * (R1 + R2) / R2
            vin *= BATTERY_CALIBRATION_FACTOR  # Aplicar calibración

            print(f"📈 AIN0 (dividido): {vout:.4f} V")
            print(f"🔋 Voltaje batería estimado: {vin:.2f} V")
            print("-" * 40)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Finalizado por el usuario.")
    finally:
        bus.close()

if __name__ == "__main__":
    main()
