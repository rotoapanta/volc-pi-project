# Configuración general para la estación meteorológica

# Rutas y almacenamiento
import os
INTERNAL_BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "DTA"))
MIN_FREE_MB = 50
MEDIA_BASE_PATH = "/media/pi"

# Identificación de la estación
STATION_NAME = "REVS2"
IDENTIFIER = 1

# Intervalos de adquisición por sensor (minutos)
RAIN_INTERVAL_MINUTES = 1
SEISMIC_INTERVAL_MINUTES = 1
GPS_INTERVAL_MINUTES = 1

# Definición del tipo de partición de archivos para almacenamiento
BLOCK_TYPE = "hour"

# Sensor de lluvia
RAIN_SENSOR_PIN = 17
FLOOD_THRESHOLD = 5
INACTIVITY_PERIOD = 30
BOUNCE_TIME = 50  # ms

# Configuración de GPS
GPS_PORT = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"
GPS_BAUDRATE = 9600
GPS_TIMEOUT = 1.0
GPS_FIX_TIMEOUT = 10.0      # segundos sin FIX antes de cambiar a SEARCHING
GPS_LOOP_SLEEP = 1.0        # segundos entre lecturas del GPS
GPS_RESYNC_ON_FIX_LOSS = True  # Si True, resinc. cada vez que el GPS recupere FIX tras perderlo
GPS_RESYNC_MIN_LOSS_SECONDS = 3600  # Tiempo mínimo de pérdida de FIX para volver a sincronizar (segundos)
GPS_SYNC_INTERVAL_SECONDS = 3600    # Intervalo de sincronización del reloj del sistema (por defecto 1 hora)

# Identificación técnica (Pluviómetro)
PLUVI_STATION_TYPE = "RGA"
PLUVI_MODEL = "rpi-5"
PLUVI_SERIAL_NUMBER = "4512"

# Identificación técnica (Sísmico)
SEISMIC_STATION_TYPE = "SIS"
SEISMIC_MODEL = "rpi-5"
SEISMIC_SERIAL_NUMBER = "4513"
SEISMIC_PORT = "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0"
SEISMIC_BAUDRATE = 9600

# Configuración de LoRa
LORA_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A36023741-if00"
LORA_BAUDRATE = 115200

# Política unificada para puertos seriales (aplicada a sísmico, GPS y futuro LoRa)
# Política unificada de reconexión serial
# - SERIAL_DISCONNECT_VERIFICATIONS: número de verificaciones rápidas al detectar desconexión
# - SERIAL_BACKGROUND_CHECK_SECONDS: intervalo del proceso en segundo plano para reintentar conexión
SERIAL_DISCONNECT_VERIFICATIONS = 3
SERIAL_BACKGROUND_CHECK_SECONDS = 30
# Retardo entre intentos rápidos para evitar múltiples logs en el mismo segundo
SERIAL_QUICK_RETRY_DELAY_SECONDS = 1
# Control de verbosidad
SERIAL_LOG_IMMEDIATE_RETRY_INFO = False
SERIAL_LOG_BACKGROUND_ERRORS = False
SERIAL_LOG_COOLDOWN = False
SERIAL_READ_DELAY = 0.2
SERIAL_BACKOFF_FACTOR = 2.0
SERIAL_MAX_BACKOFF = 2.0

# Configuración del ADS1115 (batería)
ADS1115_ADDRESS = 0x48
I2C_BUS = 1
ADS1115_CONFIG = 0xC283
ADC_RANGE = 4.096  # Volts
ADC_RESOLUTION = 32768  # 16 bits (signed)
R1 = 100_000  # 100kΩ
R2 = 15_000   # 15kΩ
BATTERY_ADC_CHANNEL = 0
#BATTERY_CALIBRATION_FACTOR = 1.0235  # Ajusta segun tu divisor resistivo
# Calibración avanzada de batería (Y = m*X + b)
BATTERY_CALIBRATION_SLOPE = 1.0222
BATTERY_CALIBRATION_OFFSET = 0.0146

# Umbrales de voltaje para estado de batería
BATTERY_LOW_VOLTAGE = 10.0       # Desde aquí se considera BAJA
BATTERY_CRITICAL_VOLTAGE = 9.5   # Desde aquí se considera CRÍTICA

# Configuración del apagado automático
BATTERY_SHUTDOWN_THRESHOLD = 9.3  # Apagar si baja de este valor
BATTERY_SHUTDOWN_CYCLES = 3       # Número de ciclos consecutivos para apagar
BATTERY_CHECK_INTERVAL = 60       # Intervalo de verificación (segundos)

GPS_MIN_SATELLITES = 5        # Para considerar señal válida
GPS_REQUIRED_FIX_QUALITY = 1  # 1 = GPS fix, 2 = DGPS fix

# Sensores configurados para el sistema (escalable)
SENSORS = [
    {
        "name": "rain",
        "type": "PLUVIOMETER",
        "code": "PLV",
        "model": "rpi-5",
        "serial": "4512",
        "interval_minutes": RAIN_INTERVAL_MINUTES,
        "pin": RAIN_SENSOR_PIN
    },
    {
        "name": "seismic",
        "type": "SEISMIC",
        "code": "SIS",
        "model": "rpi-5",
        "serial": "4513",
        "interval_minutes": SEISMIC_INTERVAL_MINUTES,  # Intervalo específico para sísmico
        "port": SEISMIC_PORT,
        "baudrate": SEISMIC_BAUDRATE
    },
    {
        "name": "gps",
        "type": "GPS",
        "code": "GPS",
        "model": "gps-neo6m",
        "serial": "gps-001",
        "interval_minutes": GPS_INTERVAL_MINUTES,  # Intervalo específico para GPS
        "port": GPS_PORT,
        "baudrate": GPS_BAUDRATE
    }
    # Puedes agregar más sensores aquí
]
