from datetime import datetime
from utils.data_schemas import seismic_schema, rain_schema, gps_schema, battery_schema

def extract_seismic(raw, now: datetime, lat=None, lon=None, alt=None):
    # Si raw es dict, tomar los valores directamente (incluye ST/ALERTA si vienen)
    if isinstance(raw, dict):
        data = {
            "LATITUD": raw.get("LATITUD", lat),
            "LONGITUD": raw.get("LONGITUD", lon),
            "ALTURA": raw.get("ALTURA", alt),
            "ALERTA": raw.get("ALERTA"),
            "PASA_BANDA": raw.get("PASA_BANDA"),
            "PASA_BAJO": raw.get("PASA_BAJO"),
            "PASA_ALTO": raw.get("PASA_ALTO"),
            "BATERIA": raw.get("BATERIA")
        }
        return seismic_schema(now, data)
    # Si raw es string, intentar extraer ST y PASA_*
    parts = raw.strip().split()
    if len(parts) >= 4:
        st = parts[0].replace('+', '')
        st = f"{int(st):03d}" if st.isdigit() else None
        alerta = (st is not None and st[0] == '1')
        data = {
            "LATITUD": lat if lat is not None else None,
            "LONGITUD": lon if lon is not None else None,
            "ALTURA": alt if alt is not None else None,
            "ALERTA": alerta,
            "PASA_BANDA": parts[1].replace('+', ''),
            "PASA_BAJO": parts[2].replace('+', ''),
            "PASA_ALTO": parts[3].replace('+', ''),
            "BATERIA": None
        }
        return seismic_schema(now, data)
    return None

def extract_rain(raw, now: datetime, lat=None, lon=None, alt=None):
    data = {
        "NIVEL": raw.get("NIVEL", 0.0),
        "LATITUD": lat if lat is not None else raw.get("LATITUD"),
        "LONGITUD": lon if lon is not None else raw.get("LONGITUD"),
        "ALTURA": alt if alt is not None else raw.get("ALTURA"),
        "BATERIA": raw.get("BATERIA")
    }
    return rain_schema(now, data)

def extract_gps(raw, now: datetime):
    return gps_schema(
        now,
        raw.get("LATITUD"),
        raw.get("LONGITUD"),
        raw.get("ALTURA"),
        raw.get("SATELITES"),
        raw.get("FIX")
    )

def extract_battery(raw, now: datetime):
    return battery_schema(
        now,
        raw.get("VOLTAGE"),
        raw.get("STATUS")
    )
