import socket
import struct
import fcntl

def get_ip_address(interface):
    """Devuelve la IP si la interfaz está conectada, None si no."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(),
                0x8915,
                struct.pack('256s', interface.encode('utf-8')[:15])
            )[20:24]
        )
    except Exception:
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
    """Devuelve lista de líneas con el estado de red."""
    lines = []
    wlan_ip = get_ip_address("wlan0")
    eth_ip = get_ip_address("eth0")

    if wlan_ip:
        lines.append(f"[ OK ] Wi-Fi conectada (wlan0 - IP: {wlan_ip})")
    else:
        lines.append("[WARN] Wi-Fi no conectada")

    if eth_ip:
        lines.append(f"[ OK ] LAN conectada (eth0 - IP: {eth_ip})")
    else:
        lines.append("[WARN] LAN no conectada")

    if is_connected():
        lines.append("[ OK ] Acceso a Internet disponible")
    else:
        lines.append("[WARN] Sin acceso a Internet")

    return lines



#Futuro uso en el sistema

 #   🔁 Reintentos de sincronización si no hay red

  #  📡 Transmisión de datos a la nube solo si hay conexión

   # 🚦 Cambiar comportamiento o guardar en buffer si la red está caída