import serial
import time

# Puerto y velocidad
PORT = "/dev/ttyUSB0"
BAUDRATE = 9600

def parse_gngga(line):
    try:
        parts = line.strip().split(',')
        if parts[0].endswith("GGA") and parts[6] != '0':
            lat_raw = parts[2]
            lat_dir = parts[3]
            lon_raw = parts[4]
            lon_dir = parts[5]
            sat_count = int(parts[7]) if parts[7] else 0
            altitude = float(parts[9]) if parts[9] else 0.0

            lat = convert_to_decimal(lat_raw, lat_dir)
            lon = convert_to_decimal(lon_raw, lon_dir)
            return lat, lon, sat_count, altitude
    except Exception:
        return None
    return None

def convert_to_decimal(value, direction):
    if not value:
        return None
    try:
        deg = int(value[:2])
        min = float(value[2:])
        decimal = deg + (min / 60)
        if direction in ['S', 'W']:
            decimal *= -1
        return round(decimal, 6)
    except:
        return None

def main():
    print("🛰️ Escuchando datos GPS desde /dev/ttyUSB0... (Ctrl+C para salir)")
    try:
        with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
            while True:
                line = ser.readline().decode('ascii', errors='ignore')
                if "$GNGGA" in line:
                    data = parse_gngga(line)
                    if data:
                        lat, lon, sats, alt = data
                        print(f"📍 Lat = {lat}°, Lon = {lon}° | 📶 Satélites = {sats} | ⛰️ Altura = {alt} m")
    except KeyboardInterrupt:
        print("\n🛑 Lectura interrumpida por el usuario.")
    except serial.SerialException as e:
        print(f"❌ Error de conexión con el puerto serie: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
