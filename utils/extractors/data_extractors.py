from datetime import datetime
from utils.data_schemas import seismic_schema, rain_schema, gps_schema, battery_schema

def extract_seismic(raw, now: datetime, lat=None, lon=None, alt=None):
    # Si raw es dict, tomar los valores directamente
    if isinstance(raw, dict):
        data = {
            "LATITUD": raw.get("LATITUD", lat),
            "LONGITUD": raw.get("LONGITUD", lon),
            "ALTURA": raw.get("ALTURA", alt),
            "PASA_BANDA": raw.get("PASA_BANDA"),
            "PASA_BAJO": raw.get("PASA_BAJO"),
            "PASA_ALTO": raw.get("PASA_ALTO"),
            "BATERIA": raw.get("BATERIA")
        }
        return seismic_schema(now, data)
    # Si raw es string, parsear como antes
    parts = raw.strip().split()
    if len(parts) >= 4:
        data = {
            "LATITUD": lat if lat is not None else None,
            "LONGITUD": lon if lon is not None else None,
            "ALTURA": alt if alt is not None else None,
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
