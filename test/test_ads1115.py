import smbus2
import time

I2C_BUS = 1
ADS1115_ADDRESS = 0x48
ADS1115_POINTER_CONVERT = 0x00
ADS1115_POINTER_CONFIG = 0x01
ADS1115_CONFIG = 0xC283  # AIN0, PGA ±4.096V, single-shot, 128SPS

bus = smbus2.SMBus(I2C_BUS)

try:
    # Configura conversión en AIN0
    config = ADS1115_CONFIG
    config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
    bus.write_i2c_block_data(ADS1115_ADDRESS, ADS1115_POINTER_CONFIG, config_bytes)
    time.sleep(0.02)
    result = bus.read_i2c_block_data(ADS1115_ADDRESS, ADS1115_POINTER_CONVERT, 2)
    raw = (result[0] << 8) | result[1]
    if raw > 0x7FFF:
        raw -= 0x10000
    print(f"Lectura cruda: {raw}")
except Exception as e:
    print(f"Error I2C: {e}")
finally:
    bus.close()
