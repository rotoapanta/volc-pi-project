import socket
import struct
import fcntl
import subprocess

def get_ip_address(interface):
    """
    Devuelve la IP si la interfaz está conectada, None si no.
    Intenta varios métodos y loguea errores y depuración.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(),
                0x8915,
                struct.pack('256s', interface.encode('utf-8')[:15])
            )[20:24]
        )
        return ip
    except Exception as e1:
        # Intento alternativo usando ip addr show
        try:
            result = subprocess.run(["ip", "addr", "show", interface], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("inet "):
                    ip = line.split()[1].split('/')[0]
                    return ip
        except Exception as e2:
            # Loguea el error si ambos métodos fallan
            try:
                from utils.log_utils import setup_logger
                logger = setup_logger("network")
                logger.warning(f"No se pudo obtener la IP de {interface}: {e1}")
            except Exception:
                pass
        return None

def is_connected():
    """Verifica acceso general a Internet."""
    try:
        socket.setdefaulttimeout(2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except socket.error:
        return False

def network_status_lines():
    """
    Devuelve (lines, conectado, wlan_ip, eth_ip): lista de tuplas (nivel, mensaje),
    estado de conexión general, y estado de interfaces.
    """
    lines = []
    wlan_ip = get_ip_address("wlan0")
    eth_ip = get_ip_address("eth0")

    if wlan_ip:
        lines.append(("info", f"Wi-Fi conectada | wlan0 - IP: {wlan_ip}"))
    else:
        lines.append(("warning", "Wi-Fi no conectada"))

    if eth_ip:
        lines.append(("info", f"LAN conectada | eth0 - IP: {eth_ip}"))
    else:
        lines.append(("warning", "LAN no conectada"))

    conectado = is_connected()
    if conectado:
        lines.append(("info", "Acceso a Internet disponible"))
    else:
        lines.append(("warning", "Sin acceso a Internet"))

    # El control de LEDs de red debe hacerse fuera de esta función usando la instancia global de LEDManager
    return lines, conectado, wlan_ip, eth_ip

# Futuro uso en el sistema
#   🔁 Reintentos de sincronización si no hay red
#   📡 Transmisión de datos a la nube solo si hay conexión
#   🚦 Cambiar comportamiento o guardar en buffer si la red está caída
