# utils/time_utils.py

import subprocess
from datetime import datetime

def sync_system_time(utc_datetime, logger=None):
    """
    Sincroniza el reloj del sistema con el datetime UTC proporcionado.
    Requiere privilegios sudo.
    
    Args:
        utc_datetime (datetime): Objeto datetime en UTC.
        logger (logging.Logger, opcional): Para registrar el evento.
        
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario.
    """
    if not isinstance(utc_datetime, datetime):
        if logger:
            logger.error("⏰ Objeto datetime inválido para sincronizar.")
        return False

    try:
        # Formatear fecha como: '2025-05-01 14:22:30'
        time_str = utc_datetime.strftime('%Y-%m-%d %H:%M:%S')
        # Ejecutar el comando date (requiere sudo)
        subprocess.run(["sudo", "date", "-u", "--set", time_str], check=True)

        if logger:
            logger.info(f"⏰ Reloj sincronizado con GPS: {time_str} UTC")

        return True
    except Exception as e:
        if logger:
            logger.error(f"❌ Error al sincronizar hora del sistema: {e}")
        return False
