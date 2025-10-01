def seismic_schema(now, data):
    return {
        "FECHA": now.strftime("%Y-%m-%d"),
        "TIEMPO": now.strftime("%H:%M:%S"),
        "LATITUD": data.get("LATITUD"),
        "LONGITUD": data.get("LONGITUD"),
        "ALTURA": data.get("ALTURA"),
        "ALERTA": data.get("ALERTA"),
        "PASA_BANDA": data.get("PASA_BANDA"),
        "PASA_BAJO": data.get("PASA_BAJO"),
        "PASA_ALTO": data.get("PASA_ALTO"),
        "BATERIA": data.get("BATERIA")
    }

def rain_schema(now, data):
    return {
        "FECHA": now.strftime("%Y-%m-%d"),
        "TIEMPO": now.strftime("%H:%M:00"),
        "LATITUD": data.get("LATITUD"),
        "LONGITUD": data.get("LONGITUD"),
        "ALTURA": data.get("ALTURA"),
        "NIVEL": data.get("NIVEL", 0.0),
        "BATERIA": data.get("BATERIA")
    }

def battery_schema(now, voltage, status):
    return {
        "FECHA": now.strftime("%Y-%m-%d"),
        "TIEMPO": now.strftime("%H:%M:00"),
        "VOLTAGE": voltage,
        "STATUS": status
    }

def gps_schema(now, lat, lon, alt, sats, fix):
    return {
        "FECHA": now.strftime("%Y-%m-%d"),
        "TIEMPO": now.strftime("%H:%M:00"),
        "LATITUD": lat,
        "LONGITUD": lon,
        "ALTURA": alt,
        "SATELITES": sats,
        "FIX": fix
    }
