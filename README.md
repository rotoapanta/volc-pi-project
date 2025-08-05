# Rain Gauge Project

Sistema profesional de monitoreo de lluvia, telemetría ambiental y sismología basado en Raspberry Pi 5

---

## Descripción

Este proyecto implementa una estación meteorológica y sísmica robusta y autónoma para la medición de precipitación (pluviómetro tipo balancín), monitoreo de batería, almacenamiento seguro de datos, telemetría GPS y adquisición de datos sísmicos por puerto USB-Serial. El sistema está diseñado para operar en campo, con almacenamiento redundante (USB y respaldo interno), indicadores LED de estado y lógica tolerante a fallos.

## Características principales

- **Pluviómetro tipo balancín**: Registro preciso de cada "tip" (pulso de lluvia) con antirrebote por hardware y software.
- **Medición de batería**: Lectura de voltaje mediante ADC ADS1115 y divisor resistivo, con umbrales configurables y lógica de apagado seguro.
- **Almacenamiento dual**: Guarda datos en memoria USB si está presente, o en almacenamiento interno si no.
- **Indicadores LED**: Estado de red, GPS, batería, almacenamiento, transmisión, error y heartbeat.
- **GPS**: Adquisición de posición, altitud y sincronización horaria con FIX robusto.
- **Sensor sísmico USB-Serial**: Integración de sensores sísmicos que envían datos por puerto serie USB, con selección robusta de puerto por symlink persistente.
- **Robustez**: Manejo de errores I2C, monitoreo dinámico de USB, lógica de histeresis para FIX GPS, logs detallados, selección de puertos USB-Serial por /dev/serial/by-id/.
- **Modularidad**: Código organizado en módulos para fácil mantenimiento y extensión.

## Requisitos

### Hardware
- Raspberry Pi 5 (recomendado)
- Pluviómetro tipo balancín (contacto seco)
- Módulo ADC ADS1115
- Módulo GPS compatible UART o USB-Serial
- Sensor sísmico con salida USB-Serial (Prolific, FTDI, etc.)
- LEDs y resistencias para indicadores (GPIO: 5, 6, 16, 22, 24, 25, 26, 27)
- Memoria USB (opcional, para almacenamiento externo)

### Software
- Raspberry Pi OS Bookworm o superior
- Python 3.9+
- Paquetes: `lgpio`, `smbus2`, `pyserial`, `gpiozero`, `shutil`, `threading`, `logging`
- Acceso a I2C y permisos de GPIO habilitados

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/rotoapanta/rain-gauge-project.git
   cd rain-gauge-project
   ```
2. Instala dependencias:
   ```bash
   sudo apt update
   sudo apt install python3-lgpio python3-smbus2 python3-pip
   pip3 install pyserial gpiozero
   ```
3. Habilita I2C y GPIO en tu Raspberry Pi (`raspi-config`)
4. Conecta el hardware según el diagrama de pines en la documentación.

## Configuración de sensores USB-Serial

Para máxima robustez, usa el symlink persistente de `/dev/serial/by-id/` para cada dispositivo USB-Serial:

1. Conecta solo el sensor sísmico y ejecuta:
   ```bash
   ls -l /dev/serial/by-id/
   ```
   Ejemplo de salida:
   ```
   usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0 -> ../../ttyUSB1
   ```
2. Copia el nombre completo y configúralo en `config.py`:
   ```python
   SEISMIC_PORT = "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0"
   SEISMIC_BAUDRATE = 9600
   ```
3. Haz lo mismo para el GPS si es USB-Serial.

## Uso

1. Ejecuta el sistema principal:
   ```bash
   python3 main.py
   ```
2. Los datos se guardarán automáticamente en la memoria USB si está presente, o en la SD interna si no.
3. Los LEDs indicarán el estado de cada subsistema (ver tabla de pines y funcionamiento abajo).
4. El log detallado se encuentra en `logs/rain_monitor.log`.
5. Los datos sísmicos se registran en el log con el prefijo `[SEISMIC]`.

## Estructura del proyecto

```
├── main.py                  # Punto de entrada principal
├── config.py                # Configuración general y de hardware
├── station/weather_station.py
├── sensors/                 # Módulos de sensores (rain, gps, ads1115, seismic, etc.)
├── utils/                   # Utilidades (leds, almacenamiento, batería, USB, logs)
├── managers/                # Lógica de alto nivel (GPS, power guard)
├── logs/                    # Logs del sistema
├── DTA/                     # Datos de lluvia almacenados
└── test/                    # Scripts de prueba de hardware
```

## Pines de LEDs

| Función   | GPIO |
|-----------|------|
| HB        | 5    |
| VOLTAGE   | 6    |
| ETH       | 16   |
| TX        | 22   |
| GPS       | 24   |
| MEDIA     | 25   |
| ERROR     | 26   |
| WIFI      | 27   |

## Estado y funcionamiento de los LEDs

| LED       | Estado         | Significado/Condición                                                        |
|-----------|---------------|----------------------------------------------------------------------------|
| HB        | Parpadeo      | Sistema encendido y funcionando correctamente (heartbeat)                   |
| VOLTAGE   | Apagado       | Voltaje normal                                                              |
| VOLTAGE   | Parpadeo lento| Batería baja                                                                |
| VOLTAGE   | Parpadeo rápido| Batería crítica                                                            |
| ETH       | Encendido     | Conexión Ethernet (cableada) activa (eth0 con IP asignada)                  |
| ETH       | Apagado       | Sin conexión Ethernet                                                       |
| WIFI      | Encendido     | Conexión WiFi activa (wlan0 con IP asignada)                                |
| WIFI      | Apagado       | Sin conexión WiFi                                                           |
| GPS       | Apagado       | Sin FIX de GPS                                                              |
| GPS       | Encendido     | FIX de GPS obtenido                                                         |
| GPS       | Parpadeo      | Buscando FIX de GPS                                                         |
| MEDIA     | Encendido     | Almacenamiento USB no detectado, usando almacenamiento interno              |
| ERROR     | Encendido     | Error crítico detectado en algún subsistema                                 |
| TX        | Encendido/Parpadeo | Indica transmisión de datos o actividad relevante                     |

> El comportamiento de los LEDs es gestionado automáticamente por el sistema según el estado de cada subsistema. No es necesario controlarlos manualmente.

## Créditos

Desarrollado por [rotoapanta](https://github.com/rotoapanta) y colaboradores.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.
