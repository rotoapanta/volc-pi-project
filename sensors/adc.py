# sensors/adc.py

import smbus2
import time
from utils.log_utils import setup_logger
from config import R1, R2, ADS1115_ADDRESS, I2C_BUS, ADS1115_CONFIG, ADC_RANGE, ADC_RESOLUTION

# Logger centralizado usando setup_logger
logger = setup_logger(__name__, log_file="adc.log")

# Registros internos del ADS1115 (no modificar)
ADS1115_POINTER_CONVERT = 0x00  # Registro de conversión / Conversion register
ADS1115_POINTER_CONFIG = 0x01   # Registro de configuración / Config register

class ADS1115Reader:
    """
    Lector para el ADC ADS1115 vía I2C.
    Permite leer valores crudos y voltajes, considerando divisor resistivo para batería.

    Reader for the ADS1115 ADC via I2C.
    Allows reading raw values and voltages, considering resistive divider for battery.
    """
    def __init__(self, bus=I2C_BUS, address=ADS1115_ADDRESS):
        """
        Inicializa el lector ADS1115 en el bus y dirección especificados.
        Raises excepción si falla la inicialización del bus I2C.

        Initializes the ADS1115 reader on the specified bus and address.
        Raises exception if I2C bus initialization fails.
        """
        try:
            self.bus = smbus2.SMBus(bus)
            self.address = address
            logger.info(f"Módulo ADC (ADS1115) inicializado | Bus: {bus} | Dirección: {hex(address)}.")
        except Exception as e:
            logger.error(f"Error al inicializar el bus I2C {bus} para ADS1115: {e}")
            raise

    def read_raw(self, channel=0):
        """
        Lee el valor crudo del canal especificado (0-3).
        Lanza ValueError si el canal es inválido.

        Reads the raw value from the specified channel (0-3).
        Raises ValueError if the channel is invalid.
        """
        if channel < 0 or channel > 3:
            logger.warning(f"Canal inválido solicitado: {channel}. Debe ser 0-3.")
            raise ValueError("Canal inválido: debe ser 0–3 / Invalid channel: must be 0–3")
        config = ADS1115_CONFIG | (channel << 12)
        config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
        self.bus.write_i2c_block_data(self.address, ADS1115_POINTER_CONFIG, config_bytes)
        time.sleep(0.02)
        result = self.bus.read_i2c_block_data(self.address, ADS1115_POINTER_CONVERT, 2)
        raw = (result[0] << 8) | result[1]
        if raw > 0x7FFF:
            raw -= 0x10000
        logger.debug(f"Lectura cruda canal {channel}: {raw}")
        return raw

    def read_channel_voltage(self, channel=0):
        """
        Convierte la lectura cruda del canal en voltios.
        Returns el voltaje medido en el canal.

        Converts the raw reading from the channel to volts.
        Returns the measured voltage on the channel.
        """
        raw = self.read_raw(channel)
        voltage = (raw * ADC_RANGE) / ADC_RESOLUTION
        logger.debug(f"Voltaje canal {channel}: {voltage:.4f} V")
        return voltage

    def read_battery_voltage(self, channel=0):
        """
        Devuelve el voltaje real de batería considerando el divisor resistivo.
        NO aplica calibración adicional (eso va en battery_utils).

        Returns the real battery voltage considering the resistive divider.
        Does NOT apply additional calibration (see battery_utils).
        """
        vout = self.read_channel_voltage(channel)
        vin = vout * (R1 + R2) / R2
        return vin

    def close(self):
        """
        Cierra el bus I2C correctamente.

        Properly closes the I2C bus.
        """
        self.bus.close()
        logger.info("Bus I2C cerrado correctamente / I2C bus closed successfully.")
