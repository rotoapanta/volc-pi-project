import time
import subprocess
from datetime import datetime, timezone
from sensors.gps import GPSReader

MIN_VALID_SATS = 5  # Umbral mínimo de satélites con fix válido


def convert_to_local_time(utc_time_str):
    """
    Convierte un string UTC ISO 8601 a hora local.
    """
    if not utc_time_str:
        return None
    try:
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
        return local_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def parse_gga(msg):
    """
    Extrae latitud, longitud, altitud y número de satélites de un mensaje GGA.
    """
    try:
        lat = msg.latitude
        lon = msg.longitude
        alt = float(msg.altitude)
        sats = int(msg.num_sats)
        fix_quality = int(msg.gps_qual)
        return lat, lon, alt, sats, fix_quality
    except Exception:
        return None, None, None, 0, 0


def wait_for_gps_fix(timeout=60):
    """
    Espera hasta que se reciba una posición válida y suficiente calidad de señal GPS.
    Devuelve un diccionario con lat, lon, alt, sats, fix_time.
    """
    gps = GPSReader()
    if not gps.connect():
        return None

    print("🛰️ Esperando señal GPS válida...")

    start = time.time()
    result = None

    try:
        while time.time() - start < timeout:
            msg = gps.read_sentence(expected=("GGA",))
            if msg and msg.sentence_type == "GGA":
                lat, lon, alt, sats, fix = parse_gga(msg)
                if fix > 0 and sats >= MIN_VALID_SATS:
                    fix_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    result = {
                        "latitude": lat,
                        "longitude": lon,
                        "altitude": alt,
                        "satellites": sats,
                        "fix_time_utc": fix_time
                    }
                    break
            time.sleep(1)
    finally:
        gps.close()

    return result


def set_system_time_from_gps():
    """
    Intenta establecer la hora del sistema desde el GPS.
    Requiere permisos de superusuario.
    """
    gps = GPSReader()
    if not gps.connect():
        return False

    print("🕓 Sincronizando hora desde GPS...")

    try:
        for _ in range(15):  # intentar durante 15 segundos
            msg = gps.read_sentence(expected=("RMC",))
            if msg and msg.datetime:
                gps_time = msg.datetime.replace(tzinfo=timezone.utc)
                formatted = gps_time.strftime("%Y-%m-%d %H:%M:%S")
                subprocess.run(["sudo", "date", "-s", formatted], check=True)
                print(f"[OK] Hora sincronizada: {formatted}")
                return True
            time.sleep(1)
    except Exception as e:
        print(f"[FAIL] No se pudo sincronizar la hora: {e}")
    finally:
        gps.close()

    return False
