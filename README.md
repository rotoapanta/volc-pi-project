# VolcPi Project

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

1. Ubica el proyecto en tu sistema:
   ```bash
   cd /home/pi/Documents/Projects/volc-pi-project
   ```
2. Instala dependencias:
   ```bash
   sudo apt update
   sudo apt install python3-lgpio python3-smbus2 python3-pip
   pip3 install pyserial gpiozero
   ```
3. Habilita I2C y GPIO en tu Raspberry Pi (`raspi-config`).
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
4. Logs del servicio en tiempo real: `sudo journalctl -u volcpi.service -f`.
5. Logs por sensor en archivos rotativos dentro de `./logs/` (por ejemplo: `seismic.log`, `gps.log`).

## Servicio systemd (arranque automático)

Este proyecto incluye un servicio systemd para ejecutar la estación automáticamente al iniciar el sistema.

- Archivo de unidad: `volcpi.service` (en la raíz del repo)
- Punto de entrada: `main.py`
- Usuario: `pi`
- Directorio de trabajo: `/home/pi/Documents/Projects/volc-pi-project`

### Instalación rápida

```bash
# Copia el archivo de servicio al directorio de systemd
sudo cp /home/pi/Documents/Projects/volc-pi-project/volcpi.service /etc/systemd/system/volcpi.service

# Recarga systemd, habilita y arranca el servicio
sudo systemctl daemon-reload
sudo systemctl enable --now volcpi.service
```

### Logs y estado

```bash
# Estado del servicio
systemctl status --no-pager volcpi.service

# Logs en tiempo real
journalctl -u volcpi.service -f -n 200
```

Los logs rotativos por archivo se guardan además en el directorio `./logs/` del proyecto.

### Comandos útiles de administración del servicio

```bash
# Iniciar / Detener / Reiniciar
sudo systemctl start volcpi.service
sudo systemctl stop volcpi.service
sudo systemctl restart volcpi.service

# Estado e información
systemctl status --no-pager volcpi.service
systemctl is-active volcpi.service
systemctl is-enabled volcpi.service

# Habilitar / Deshabilitar en el arranque
sudo systemctl enable volcpi.service
sudo systemctl disable volcpi.service

# Recargar definición del servicio tras editar el archivo .service
sudo systemctl daemon-reload

# Logs
journalctl -u volcpi.service -n 200 --no-pager
journalctl -u volcpi.service -f
```

### Actualizar el servicio tras cambios
Si editas `volcpi.service` o `main.py` y quieres aplicar los cambios:

```bash
sudo systemctl daemon-reload
sudo systemctl restart volcpi.service
```

### Requisitos del sistema (permisos y paquetes)

- Paquetes (Debian/Raspberry Pi OS):
  ```bash
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip python3-serial python3-lgpio python3-smbus2 python3-pynmea2 i2c-tools
  ```
- Grupos (para acceso a GPIO/I2C/Serial):
  ```bash
  sudo usermod -aG gpio,i2c,dialout pi
  sudo reboot
  ```
- Habilitar I2C si no lo está (raspi-config o equivalente).

> Nota sobre GPIO/Serial/I2C: con los grupos dialout,gpio,i2c configurados, no se requieren capacidades especiales en el servicio.

### Sincronización horaria por GPS (opcional pero recomendado)
El código sincroniza la hora del sistema con el GPS ejecutando `sudo date -u --set ...`. Para que funcione de forma no interactiva:

- Opción A (recomendada): permitir `date` sin contraseña para `pi`.
  ```bash
  sudo visudo -f /etc/sudoers.d/volcpi
  # Añadir esta línea y guardar:
  # pi ALL=(root) NOPASSWD: /bin/date
  ```
- Opción B: quitar "sudo" en el código y otorgar capacidad de tiempo al servicio.
  - Editar el unit para incluir:
    ```ini
    AmbientCapabilities=CAP_SYS_TIME
    CapabilityBoundingSet=CAP_SYS_TIME
    ```
  - Requiere que la llamada use `/bin/date` sin `sudo`.

### Robustez de arranque (opcional)
- Asegurar que udev haya creado los dispositivos seriales antes de arrancar:
  ```ini
  ExecStartPre=/usr/bin/udevadm settle
  ```
- El unit ya incluye `ExecStartPre=/bin/sleep 3` para dar tiempo a hardware/OS.
- El almacenamiento USB se detecta en `/media/pi/...`. En sistemas headless sin automontaje, configura un automount o fstab si necesitas montaje al arranque.

### Desinstalación

```bash
sudo systemctl disable --now volcpi.service
sudo rm /etc/systemd/system/volcpi.service
sudo systemctl daemon-reload
```

## Estructura del proyecto

```
├── main.py                  # Punto de entrada principal
├── config.py                # Configuración general y de hardware
├── volcpi.service           # Unidad systemd del servicio
├── diagnostics/
│   └── startup.py
├── managers/                # Lógica de alto nivel (seismic, rain, gps, etc.)
│   ├── battery_manager.py
│   ├── gps_manager.py
│   ├── lora_manager.py
│   ├── rain_manager.py
│   └── seismic_manager.py
├── sensors/                 # Módulos de sensores (rain, gps, ads1115, seismic, etc.)
│   ├── adc.py
│   ├── base_sensor.py
│   ├── gps.py
│   ├── lora.py
│   ├── network.py
│   ├── rain.py
│   └── seismic.py
├── station/
│   └── monitoring_station.py
├── utils/                   # Utilidades (leds, almacenamiento, batería, USB, logs)
│   ├── extractors/
│   │   └── data_extractors.py
│   ├── sensors/
│   │   ├── battery_utils.py
│   │   ├── gps_utils.py
│   │   ├── seismic_utils.py
│   │   └── time_utils.py
│   ├── storage/
│   │   ├── block_storage.py
│   │   ├── migrate_to_usb.py
│   │   └── storage_utils.py
│   ├── battery_guard.py
│   ├── data_schemas.py
│   ├── generic_storage.py
│   ├── leds_monitor.py
│   ├── leds_utils.py
│   ├── log_utils.py
│   └── network_monitor.py
├── test/
│   ├── test_serial_input.py
│   ├── test_serial_seismic.py
│   ├── test_leds.py
│   └── ...
├── logs/                    # Logs del sistema (archivos rotativos)
└── DTA/                     # Datos almacenados
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

## Mensajes de Log del Sistema

A continuación se listan los principales mensajes de log generados por el sistema (especialmente en el arranque):

| Nivel   | Mensaje / Formato                                                                                 | Contexto / Descripción                                                        |
|---------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| INFO    | ==================== INICIALIZACIÓN DEL SISTEMA ====================                              | Inicio del proceso de arranque                                                |
| INFO    | Estación activa: {STATION_NAME} - Intervalo de adquisición: {RAIN_INTERVAL_MINUTES} min           | Nombre de estación y frecuencia de adquisición                                |
| WARNING | No se pudo mostrar mensaje de estación activa: {e}                                                | Error al mostrar el mensaje de estación                                       |
| INFO    | Sensor de lluvia configurado | GPIO: {RAIN_SENSOR_PIN}                                            | Sensor de lluvia detectado y configurado                                      |
| ERROR   | Sensor de lluvia: error al configurar ({e})                                                       | Error al configurar el sensor de lluvia                                       |
| INFO    | Memoria USB detectada | Ruta: {usb} | Espacio libre: {free_mb} MB                                 | USB detectada y espacio disponible                                            |
| WARNING | Memoria USB: espacio bajo (<{MIN_FREE_MB} MB)                                                     | Espacio en USB por debajo del umbral                                          |
| ERROR   | Memoria USB: error al acceder ({e})                                                               | Error al acceder a la memoria USB                                             |
| WARNING | Memoria USB no detectada | Usando almacenamiento interno: {local_path}                            | No se detecta USB, se usa almacenamiento interno                              |
| INFO    | Espacio local configurado | Ruta: {local_path} | Espacio libre: {local_free_mb} MB                | Espacio disponible en almacenamiento interno                                  |
| ERROR   | Espacio local: error al verificar ({e})                                                           | Error al verificar espacio local                                              |
| INFO    | GPS configurado | Puerto: {gps_port_short} | Baudrate: {GPS_BAUDRATE} | Sync interval: {GPS_SYNC_INTERVAL_SECONDS} s | GPS detectado y configurado                                         |
| DEBUG   | GPS: módulo no implementado o error ({e})                                                         | GPS no implementado o error                                                   |
| INFO    | Módulo sísmico configurado | Puerto: {seismic_port_short} | Baudrate: {SEISMIC_BAUDRATE} | Intervalo: {SEISMIC_INTERVAL_MINUTES} min | Módulo sísmico detectado y configurado |
| WARNING | Módulo sísmico: error al inicializar ({e})                                                        | Error al inicializar el módulo sísmico                                        |
| INFO    | LoRa: módulo no implementado aún                                                                  | Placeholder para LoRa                                                         |
| DEBUG   | Estado LoRa: no implementado                                                                      | Placeholder para LoRa                                                         |
| INFO    | 🔋 Voltaje de batería inicial: {battery_info['voltage']:.2f} V - {battery_info['status']}         | Voltaje y estado de la batería al inicio                                      |
| WARNING | Voltaje de batería inicial: ERROR ({battery_info['status']})                                      | Error al leer el voltaje de batería                                           |
| WARNING | ⚠️ Nivel de batería bajo                                                                          | Batería en estado BAJA                                                        |
| ERROR   | 🔋 Error al leer voltaje de batería inicial - Estado: {battery_info['status']}                    | Error crítico al leer voltaje de batería                                      |
| INFO    | ===================================================================                              | Fin del bloque de inicialización                                              |

> Los mensajes pueden contener variables entre llaves `{}` que se reemplazan en tiempo de ejecución.

## Créditos

Desarrollado por [rotoapanta](https://github.com/rotoapanta) y colaboradores.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.
