import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
import sys

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str,
    log_file: str = None,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5,
    when: str = None,  # e.g. 'midnight' for daily rotation
    encoding: str = "utf-8"
):
    """
    Configura y retorna un logger profesional con rotación y formato consistente.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    # Evita handlers duplicados
    if logger.hasHandlers():
        logger.handlers.clear()

    # Handler para archivo con rotación
    if log_file:
        log_path = os.path.join(LOG_DIR, log_file)
        if when:
            handler = TimedRotatingFileHandler(
                log_path, when=when, backupCount=backup_count, encoding=encoding
            )
        else:
            handler = RotatingFileHandler(
                log_path, maxBytes=max_bytes, backupCount=backup_count, encoding=encoding
            )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Handler para consola (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def log_and_print(prefix, data, logger, keys=None, level=logging.INFO):
    """
    Imprime y loguea un mensaje con formato consistente.
    """
    if keys:
        msg = f"{prefix} " + " ".join(f"{k}={data.get(k)}" for k in keys)
    else:
        msg = f"{prefix} {data}"
    print(msg)
    if logger:
        logger.log(level, msg)
