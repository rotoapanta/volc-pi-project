import pynmea2

# Línea NMEA real de tu GPS
linea = "$GNGGA,210706.00,0012.72446,S,07829.48651,W,1,09,1.15,2811.1,M,13.8,M,,*78"

# Parsear la línea
mensaje = pynmea2.parse(linea)

# Mostrar los campos importantes
print(f"⏰ Hora UTC:       {mensaje.timestamp}")
print(f"🌐 Latitud:        {mensaje.latitude} {mensaje.lat_dir}")
print(f"🌐 Longitud:       {mensaje.longitude} {mensaje.lon_dir}")
print(f"📡 Satélites:      {mensaje.num_sats}")
print(f"📶 Calidad señal:  {mensaje.gps_qual}")
print(f"🗻 Altitud (m):     {mensaje.altitude}")
