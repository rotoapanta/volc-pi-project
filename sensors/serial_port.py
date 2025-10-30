# sensors/serial_port.py

import time
import os
import serial
from utils.log_utils import setup_logger
from config import (
    SERIAL_DISCONNECT_VERIFICATIONS,
    SERIAL_BACKGROUND_CHECK_SECONDS,
    SERIAL_QUICK_RETRY_DELAY_SECONDS,
    SERIAL_LOG_IMMEDIATE_RETRY_INFO,
    SERIAL_LOG_BACKGROUND_ERRORS,
    SERIAL_LOG_COOLDOWN,
    SERIAL_READ_DELAY,
    SERIAL_BACKOFF_FACTOR,
    SERIAL_MAX_BACKOFF,
)


class RobustSerial:
    """
    Manejador robusto para puertos seriales con:
    - Reintentos controlados de apertura
    - Periodo de cooldown tras N fallos consecutivos
    - Backoff para lecturas/reconexiones
    - Logging consistente y no ruidoso

    Uso típico:
        rs = RobustSerial(port, baudrate, timeout, logger=logger)
        line = rs.readline()
        if line:
            ...
    """

    def __init__(
        self,
        port,
        baudrate=9600,
        timeout=1,
        logger=None,
        # Política por defecto (puede ser parametrizada desde config)
        max_open_failures=5,
        open_cooldown_seconds=30,
        read_delay=None,
        backoff_factor=None,
        max_backoff=None,
        name=None,
        disconnect_verifications=None,
        background_check_seconds=None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.logger = logger or setup_logger("robust_serial", log_file="serial.log")
        self.name = name

        # Estado
        self.ser = None
        self._consecutive_open_failures = 0
        self._cooldown_until = 0
        # Verbosity control flags
        self._open_error_reported = False
        self._read_error_reported = False

        # Política
        self.max_open_failures = max_open_failures
        self.open_cooldown_seconds = open_cooldown_seconds
        self.read_delay = SERIAL_READ_DELAY if read_delay is None else read_delay
        self.backoff_factor = SERIAL_BACKOFF_FACTOR if backoff_factor is None else backoff_factor
        self.max_backoff = SERIAL_MAX_BACKOFF if max_backoff is None else max_backoff
        # Verificación inmediata vs. proceso en segundo plano
        self.disconnect_verifications = (
            SERIAL_DISCONNECT_VERIFICATIONS if disconnect_verifications is None else disconnect_verifications
        )
        self.background_check_seconds = (
            SERIAL_BACKGROUND_CHECK_SECONDS if background_check_seconds is None else background_check_seconds
        )
        self._immediate_tries_left = self.disconnect_verifications
        self._next_background_check = 0
        # Contadores de intentos para logging
        self._attempt_counter_bg = 0

    def _id(self):
        """Etiqueta corta para logs: nombre si existe, sino basename del puerto."""
        if self.name:
            return self.name
        try:
            base = os.path.basename(str(self.port))
            return base or str(self.port)
        except Exception:
            return str(self.port)

    def is_open(self):
        return bool(self.ser and getattr(self.ser, "is_open", False))

    def _err_code(self, e):
        """Retorna un identificador corto del error para logs sin paths largos."""
        try:
            code = getattr(e, 'errno', None)
            # Si no hay errno o viene vacío, usar nombre de excepción
            if code in (None, '', 0):
                return e.__class__.__name__
            # Intentar convertir a entero legible
            try:
                icode = int(code)
                if icode != 0:
                    return f"errno={icode}"
            except Exception:
                # No entero: usar string corto si existe
                s = str(code).strip()
                if s:
                    return s
            # Último recurso
            return e.__class__.__name__
        except Exception:
            return e.__class__.__name__

    def open(self):
        """Intenta abrir el puerto con dos fases:
        1) Verificación rápida N veces (disconnect_verifications)
        2) Si falla, revisa en segundo plano cada background_check_seconds
        Mantiene supresión de logs repetidos y reconexión automática al aparecer.
        """
        now = time.time()
        # Si está en cooldown, respetarlo
        if self._cooldown_until and now < self._cooldown_until:
            return False
        # Fase 2: si agotó intentos rápidos, sólo permitir intento cuando toque el background check
        if self._immediate_tries_left <= 0 and now < self._next_background_check:
            return False
        try:
            if self.is_open():
                return True
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            # Éxito -> reset contadores/flags y volver a fase 1
            self._consecutive_open_failures = 0
            self._cooldown_until = 0
            self._open_error_reported = False
            self._read_error_reported = False
            self._immediate_tries_left = self.disconnect_verifications
            self._next_background_check = 0
            # Reset contadores
            self._attempt_counter_bg = 0
            # Notificar conexión/reconexión
            try:
                if self.logger:
                    self.logger.info(
                        f"Puerto serial {self._id()}: reconectado" if self._open_error_reported else f"Puerto serial {self._id()}: conectado"
                    )
            except Exception:
                pass
            return True
        except Exception as e:
            # Intento fallido
            if self._immediate_tries_left > 0:
                # Fase de verificaciones rápidas: enumerar intento y espaciar
                idx = self.disconnect_verifications - self._immediate_tries_left + 1
                if self.logger and SERIAL_LOG_IMMEDIATE_RETRY_INFO:
                    self.logger.info(f"Reintento {self._id()} {idx}/{self.disconnect_verifications} fallido")
                if self.logger and not self._open_error_reported:
                    self.logger.error(f"Fallo en el puerto serial {self._id()} (intento {idx}/{self.disconnect_verifications}): {self._err_code(e)}")
                    self._open_error_reported = True
                # Espera configurable para no generar múltiples logs en el mismo segundo
                try:
                    time.sleep(max(0.0, float(SERIAL_QUICK_RETRY_DELAY_SECONDS)))
                except Exception:
                    time.sleep(1)
            else:
                # Fase en segundo plano: enumerar contadores de background en el primer detalle
                self._attempt_counter_bg += 1
                if self.logger and (not self._open_error_reported) and SERIAL_LOG_BACKGROUND_ERRORS:
                    self.logger.error(f"Fallo en el puerto serial {self._id()} (background #{self._attempt_counter_bg}): {self._err_code(e)}")
                    self._open_error_reported = True
            # Control de fallos y programación de reintentos
            self._consecutive_open_failures += 1
            if self._immediate_tries_left > 0:
                self._immediate_tries_left -= 1
                if self._immediate_tries_left == 0:
                    # Pasar a verificación en segundo plano
                    self._next_background_check = now + self.background_check_seconds
                    if self.logger and SERIAL_LOG_COOLDOWN:
                        self.logger.warning(
                            f"Puerto serial {self._id()}: verificando en segundo plano cada {self.background_check_seconds}s"
                        )
            else:
                # Reprogramar siguiente chequeo en segundo plano
                self._next_background_check = now + self.background_check_seconds
            # Mantener también el cooldown para ráfagas de fallos consecutivos
            if self._consecutive_open_failures >= self.max_open_failures:
                self._cooldown_until = now + self.open_cooldown_seconds
                if self.logger and SERIAL_LOG_COOLDOWN:
                    self.logger.warning(
                        f"Puerto serial {self._id()}: fallos consecutivos >= {self.max_open_failures}. Cooldown {self.open_cooldown_seconds}s"
                    )
                self._consecutive_open_failures = 0
                self._open_error_reported = False
            return False

    def close(self):
        try:
            if self.ser and getattr(self.ser, "is_open", False):
                self.ser.close()
        except Exception:
            pass
        finally:
            self.ser = None

    def readline(self):
        """
        Lee una línea del puerto serial de forma robusta.
        - Si no está abierto, intenta abrir (respetando cooldown)
        - Si falla la lectura por SerialException, cierra y aplica backoff breve
        - Retorna bytes o None si no hay datos/puerto
        """
        # Intentar abrir si es necesario
        if not self.is_open():
            opened = self.open()
            if not opened:
                # Si hay cooldown activo o fallo de apertura, no spamear
                # Devolver None para que el caller decida cuándo reintentar
                return None

        try:
            data = self.ser.readline()
            return data if data else None
        except serial.SerialException as e:
            if self.logger and not self._read_error_reported:
                self.logger.error(f"Error de lectura en puerto serial {self._id()}: {self._err_code(e)}")
                self._read_error_reported = True
            # Cerrar y breve backoff; el caller puede reintentar
            self.close()
            time.sleep(min(self.read_delay * self.backoff_factor, self.max_backoff))
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error genérico de lectura en puerto serial {self._id()}: {self._err_code(e)}")
            time.sleep(0.05)
            return None
