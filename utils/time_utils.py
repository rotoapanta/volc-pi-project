import subprocess
from datetime import datetime

def set_system_time_from_gps(timestamp):
    """
    Convierte el tiempo del GPS (tipo datetime.time) a un comando para actualizar la hora del sistema.
    """
    if not isinstance(timestamp, datetime.time):
        return

    now = datetime.utcnow()
    new_time = datetime.combine(now.date(), timestamp)
    formatted_time = new_time.strftime("%Y-%m-%d %H:%M:%S")
    subprocess.call(["sudo", "date", "-s", formatted_time])
