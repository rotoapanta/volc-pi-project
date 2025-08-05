import os
import shutil
import logging

def migrate_internal_to_usb(internal_dir, usb_dir, logger=None):
    """
    Mueve todos los archivos de internal_dir a usb_dir, preservando la estructura de carpetas.
    Si un archivo ya existe en destino, lo sobrescribe.
    """
    if logger is None:
        logger = logging.getLogger("migrate_to_usb")
    files_migrated = 0
    for root, dirs, files in os.walk(internal_dir):
        rel_path = os.path.relpath(root, internal_dir)
        dest_root = os.path.join(usb_dir, rel_path) if rel_path != '.' else usb_dir
        os.makedirs(dest_root, exist_ok=True)
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_root, file)
            try:
                shutil.move(src_file, dest_file)
                logger.info(f"[MIGRACION] {src_file} -> {dest_file}")
                files_migrated += 1
            except Exception as e:
                logger.error(f"[MIGRACION][ERROR] No se pudo mover {src_file} -> {dest_file}: {e}")
    logger.info(f"[MIGRACION] Total archivos migrados: {files_migrated}")
    return files_migrated
