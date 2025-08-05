import os
import subprocess
import shutil
from utils.log_utils import setup_logger

logger = setup_logger("usb_manager")

MEDIA_BASE_PATH = "/media/pi"
MIN_FREE_MB = 50

def list_usb_devices():
    """
    Devuelve una lista de dispositivos USB montados con sus etiquetas y espacio disponible.
    """
    devices = []
    try:
        for label in os.listdir(MEDIA_BASE_PATH):
            path = os.path.join(MEDIA_BASE_PATH, label)
            if os.path.ismount(path):
                stat = shutil.disk_usage(path)
                devices.append({
                    "label": label,
                    "path": path,
                    "total_mb": stat.total // (1024 * 1024),
                    "free_mb": stat.free // (1024 * 1024),
                    "used_mb": stat.used // (1024 * 1024)
                })
    except Exception as e:
        logger.error(f"No se pudieron listar las memorias USB: {e}")
    return devices

def find_primary_usb(min_free_mb=MIN_FREE_MB):
    """
    Encuentra la primera memoria USB con espacio suficiente.
    """
    devices = list_usb_devices()
    for dev in devices:
        if dev["free_mb"] >= min_free_mb:
            return dev
    return None

def format_usb(device_path, fs_type="vfat", label="RAINDATA"):
    """
    Formatea una unidad USB. ¡Este proceso borra todos los datos!
    """
    if not os.path.ismount(device_path):
        logger.error(f"{device_path} no está montada. Aborta formateo.")
        return False

    # Detectar el dispositivo (por ejemplo, /dev/sda1) usando `df`
    try:
        df_output = subprocess.check_output(["df", device_path], text=True).splitlines()
        if len(df_output) < 2:
            logger.error("No se pudo determinar el dispositivo desde df.")
            return False
        device = df_output[1].split()[0]
    except Exception as e:
        logger.error(f"Error al ejecutar df para {device_path}: {e}")
        return False

    # Desmontar la unidad
    try:
        subprocess.check_call(["umount", device_path])
        logger.info(f"Dispositivo {device_path} desmontado.")
    except Exception as e:
        logger.error(f"No se pudo desmontar {device_path}: {e}")
        return False

    # Formatear
    try:
        if fs_type == "vfat":
            subprocess.check_call(["mkfs.vfat", "-F", "32", "-n", label, device])
        elif fs_type == "ext4":
            subprocess.check_call(["mkfs.ext4", "-F", "-L", label, device])
        else:
            logger.error(f"Sistema de archivos no soportado: {fs_type}")
            return False
        logger.info(f"{device} formateado como {fs_type} con etiqueta {label}")
        return True
    except Exception as e:
        logger.error(f"Error al formatear {device}: {e}")
        return False
