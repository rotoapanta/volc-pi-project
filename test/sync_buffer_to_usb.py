import os
import shutil
import logging

BUFFER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DTA")
USB_PATH = "/media/pi/BALER44/DTA"

logger = logging.getLogger("sync")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def copy_recursive(src, dst):
    if not os.path.exists(src):
        logger.warning(f"Directorio fuente no existe: {src}")
        return

    for root, dirs, files in os.walk(src):
        relative_path = os.path.relpath(root, src)
        target_dir = os.path.join(dst, relative_path)
        os.makedirs(target_dir, exist_ok=True)

        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_dir, file)

            if not os.path.exists(dst_file):
                try:
                    shutil.copy2(src_file, dst_file)
                    logger.info(f"📁 Copiado: {src_file} -> {dst_file}")
                except Exception as e:
                    logger.error(f"❌ Error al copiar {src_file}: {e}")
            else:
                logger.info(f"🔁 Ya existe, omitido: {dst_file}")

def sync_buffer_to_usb():
    if not os.path.ismount("/media/pi/BALER44"):
        logger.error("USB no está montada. Abortando sincronización.")
        return

    logger.info("🔄 Iniciando sincronización de respaldo interno hacia USB...")
    copy_recursive(BUFFER_PATH, USB_PATH)
    logger.info("✅ Sincronización completada.")

if __name__ == "__main__":
    sync_buffer_to_usb()
