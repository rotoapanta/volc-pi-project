# sensors/lora.py

from sensors.serial_port import RobustSerial
from utils.log_utils import setup_logger


class LoRaSerial:
    """
    Plantilla para módulo LoRa basada en RobustSerial.
    - Manejo unificado de reintentos / cooldown / logs concisos
    - Métodos simples de enviar / recibir
    """
    def __init__(
        self,
        port,
        baudrate=115200,
        timeout=1,
        logger=None,
        max_open_failures=5,
        open_cooldown_seconds=30,
        read_delay=0.2,
        backoff_factor=2.0,
        max_backoff=2.0,
    ):
        self.logger = logger or setup_logger("lora", log_file="lora.log")
        self.ser = RobustSerial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            logger=self.logger,
            max_open_failures=max_open_failures,
            open_cooldown_seconds=open_cooldown_seconds,
            read_delay=read_delay,
            backoff_factor=backoff_factor,
            max_backoff=max_backoff,
            name="LORA",
        )

    def write_line(self, text: str) -> bool:
        """Envía una línea (terminada en \r\n). Retorna True si parece OK."""
        if not self.ser.is_open() and not self.ser.open():
            return False
        try:
            data = (text + "\r\n").encode("utf-8")
            self.ser.ser.write(data)
            return True
        except Exception as e:
            if self.logger:
                # logs concisos, RobustSerial gestiona reconexiones
                self.logger.error(f"Error al enviar a LORA: {e.__class__.__name__}")
            self.ser.close()
            return False

    def read_line(self):
        """Lee una línea cruda desde LoRa; retorna str o None."""
        data = self.ser.readline()
        if not data:
            return None
        try:
            return data.decode("utf-8", errors="ignore").strip()
        except Exception:
            return str(data, errors="ignore").strip()

    def close(self):
        self.ser.close()
