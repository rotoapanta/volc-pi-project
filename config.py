# Configuración general para la estación meteorológica

# Identificación de la estación
STATION_NAME = "REVS2"
IDENTIFIER = 1

# Intervalo de adquisición (minutos)
ACQUISITION_INTERVAL = 1

# Sensor de lluvia
RAIN_SENSOR_PIN = 17
FLOOD_THRESHOLD = 5
INACTIVITY_PERIOD = 30
BOUNCE_TIME = 300  # ms

# Identificación técnica
TIPO_ESTACION = "RGA"
MODEL = "rpi-5"
SERIAL_NUMBER = "4512"

# Configuración del ADS1115 (batería)
ADS1115_ADDRESS = 0x4B
BATTERY_ADC_CHANNEL = 0
#BATTERY_CALIBRATION_FACTOR = 1.0235  # Ajusta según tu divisor resistivo
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


# Configuración de GPS
GPS_PORT = "/dev/ttyUSB0"
GPS_BAUDRATE = 9600
GPS_TIMEOUT = 1.0

GPS_MIN_SATELLITES = 5        # Para considerar señal válida
GPS_REQUIRED_FIX_QUALITY = 1  # 1 = GPS fix, 2 = DGPS fix
