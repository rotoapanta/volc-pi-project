import logging
import os
from logging.handlers import RotatingFileHandler

class ColorFormatter(logging.Formatter):
    COLOR_SEISMIC = "\033[1;33m"
    COLOR_PLUVIOMETER = "\033[1;36m"
    COLOR_GPS = "\033[1;35m"
    COLOR_BATTERY = "\033[1;32m"
    COLOR_RESET = "\033[0m"

    def format(self, record):
        msg = super().format(record)
        if "[SEISMIC]" in msg:
            return f"{self.COLOR_SEISMIC}{msg}{self.COLOR_RESET}"
        elif "[PLUVIOMETER]" in msg:
            return f"{self.COLOR_PLUVIOMETER}{msg}{self.COLOR_RESET}"
        elif "[GPS]" in msg:
            return f"{self.COLOR_GPS}{msg}{self.COLOR_RESET}"
        elif "[BATTERY]" in msg:
            return f"{self.COLOR_BATTERY}{msg}{self.COLOR_RESET}"
        return msg

def setup_logger(name="rain_monitor", log_dir="logs", level=logging.INFO):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Archivo rotativo
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f"{name}.log"), maxBytes=5_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]

    # Handler de consola con color
    ch = logging.StreamHandler()
    color_formatter = ColorFormatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(color_formatter)
    logger.addHandler(ch)

    return logger
