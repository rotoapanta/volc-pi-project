import os
import shutil
import logging
import hashlib


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _remove_empty_dirs(root_dir, logger):
    removed = 0
    for current_root, dirs, files in os.walk(root_dir, topdown=False):
        if current_root == root_dir:
            continue
        try:
            if not os.listdir(current_root):
                os.rmdir(current_root)
                removed += 1
        except Exception as e:
            logger.warning(f"No se pudo eliminar directorio vacío {current_root}: {e}")
    return removed


def migrate_internal_to_usb(internal_dir, usb_dir, logger=None):
    """
    Migra archivos de internal_dir a usb_dir preservando estructura.
    - Si no existe en destino: mover.
    - Si existe en destino y es idéntico (sha256): eliminar origen y registrar como duplicado omitido.
    - Si existe y difiere: conservar ambos; se mueve como <nombre>.conflict-<hash8> y se loguea conflicto.

    Retorna: cantidad de archivos movidos (excluye duplicados omitidos).
    """
    if logger is None:
        logger = logging.getLogger("migrate_to_usb")
    files_migrated = 0
    files_duplicates = 0
    files_conflicts = 0
    for root, dirs, files in os.walk(internal_dir):
        rel_path = os.path.relpath(root, internal_dir)
        dest_root = os.path.join(usb_dir, rel_path) if rel_path != '.' else usb_dir
        os.makedirs(dest_root, exist_ok=True)
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_root, file)
            try:
                if os.path.exists(dest_file):
                    try:
                        src_hash = _sha256(src_file)
                        dest_hash = _sha256(dest_file)
                        if src_hash == dest_hash:
                            # Duplicado idéntico: omitir mover, eliminar origen
                            try:
                                os.remove(src_file)
                                logger.info(f"Duplicado omitido (idéntico): {src_file} == {dest_file}")
                                files_duplicates += 1
                            except Exception as er:
                                logger.warning(f"No se pudo eliminar duplicado de origen: {src_file} ({er})")
                            continue
                        else:
                            # Conflicto: conservar ambos
                            conflict_name = f"{file}.conflict-{src_hash[:8]}"
                            conflict_path = os.path.join(dest_root, conflict_name)
                            shutil.move(src_file, conflict_path)
                            logger.warning(f"Conflicto de contenido: {src_file} -> {conflict_path} (destino existente: {dest_file})")
                            files_conflicts += 1
                            continue
                    except Exception as eh:
                        logger.warning(f"Error comparando hashes, sobrescribiendo: {src_file} -> {dest_file} ({eh})")
                        shutil.move(src_file, dest_file)
                        files_migrated += 1
                        logger.info(f"Migración: {src_file} -> {dest_file}")
                else:
                    shutil.move(src_file, dest_file)
                    files_migrated += 1
                    logger.info(f"Migración: {src_file} -> {dest_file}")
            except Exception as e:
                logger.error(f"No se pudo mover {src_file} -> {dest_file}: {e}")
    logger.info(f"Total migrados: {files_migrated} | duplicados omitidos: {files_duplicates} | conflictos: {files_conflicts}")
    # Limpieza de directorios vacíos en almacenamiento interno (mantiene la raíz)
    try:
        removed_dirs = _remove_empty_dirs(internal_dir, logger)
        if removed_dirs:
            logger.info(f"Directorios vacíos eliminados en {internal_dir}: {removed_dirs}")
    except Exception as e:
        logger.warning(f"Error durante la limpieza de directorios vacíos en {internal_dir}: {e}")
    return files_migrated
