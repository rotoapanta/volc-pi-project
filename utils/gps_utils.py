# utils/gps_utils.py

import pynmea2
from datetime import datetime
import os
import subprocess

def parse_nmea_sentence(nmea_sentence):
    """
    Parsea una sentencia NMEA usando pynmea2.
    Retorna el objeto de mensaje o None si es inválido.
    """
    try:
        return pynmea2.parse(nmea_sentence)
    except pynmea2.ParseError:
        return None

def extract_coordinates(nmea_msg):
    """
    Extrae latitud y longitud de una sentencia NMEA válida.
    Retorna (lat, lon) en decimal o None si no aplica.
    """
    if hasattr(nmea_msg, 'latitude') and hasattr(nmea_msg, 'longitude'):
        return round(nmea_msg.latitude, 6), round(nmea_msg.longitude, 6)
    return None

def extract_altitude(nmea_msg):
    """
    Extrae altitud (en metros) de una sentencia GGA válida.
    """
    if isinstance(nmea_msg, pynmea2.types.talker.GGA):
        try:
            return float(nmea_msg.altitude)
        except (ValueError, TypeError):
            return None
    return None

def extract_satellite_count(nmea_msg):
    """
    Retorna el número de satélites en uso si es una sentencia GGA.
    """
    if isinstance(nmea_msg, pynmea2.types.talker.GGA):
        try:
            return int(nmea_msg.num_sats)
        except (ValueError, TypeError):
            return None
    return None

def extract_utc_time(nmea_msg):
    """
    Retorna una cadena de tiempo UTC a partir de sentencias GGA o RMC.
    """
    if hasattr(nmea_msg, 'timestamp'):
        now = datetime.utcnow()
        t = nmea_msg.timestamp
        return datetime(now.year, now.month, now.day, t.hour, t.minute, t.second)
    return None

def sync_system_clock(utc_datetime):
    """
    Sincroniza el reloj del sistema con el tiempo UTC proporcionado (requiere privilegios).
    """
    if utc_datetime is None:
        return False
    try:
        time_str = utc_datetime.strftime('%Y-%m-%d %H:%M:%S')
        subprocess.run(["sudo", "date", "-u", "--set", time_str], check=True)
        return True
    except Exception as e:
        from utils.print_utils import print_colored
        print_colored(f"[ERROR] No se pudo sincronizar la hora del sistema: {e}")
        return False
