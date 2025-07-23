# test/test_time_sync.py

import sys
import os
from datetime import datetime, timezone

# Añadir el directorio raíz del proyecto al path para importar correctamente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.time_utils import sync_system_time
import logging

# Configuración de logging simple
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("time_test")

# Simular un datetime UTC válido
utc_time = datetime(2025, 5, 1, 15, 30, 0, tzinfo=timezone.utc)

# Ejecutar sincronización
print("⏳ Intentando sincronizar la hora del sistema...")
success = sync_system_time(utc_time, logger)

if success:
    print("✅ Sincronización completada con éxito.")
else:
    print("❌ Falló la sincronización. Verifica permisos o formato.")
