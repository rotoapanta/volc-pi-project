import serial
import sys
from datetime import datetime

# Configuración por defecto
DEFAULT_PORT = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'  # Cambia esto según tu sistema (ej: 'COM1' en Windows)
DEFAULT_BAUDRATE = 9600

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PORT
    baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BAUDRATE
    print(f"Abriendo puerto serial {port} a {baudrate} baudios...")
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            print("Leyendo datos. Presiona Ctrl+C para salir.")
            prev_time = None
            while True:
                line = ser.readline()
                if line:
                    now = datetime.now()
                    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
                    if prev_time is not None:
                        delta = (now - prev_time).total_seconds()
                        print(f"[{timestamp}] {line.decode(errors='replace').strip()}  (+{delta:.2f} s)")
                    else:
                        print(f"[{timestamp}] {line.decode(errors='replace').strip()}")
                    prev_time = now
    except serial.SerialException as e:
        print(f"[ERROR] No se pudo abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("\nLectura finalizada por el usuario.")
