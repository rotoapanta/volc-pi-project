#!/usr/bin/env python3
import argparse
import glob
import json
import sys
from datetime import datetime

import serial

from utils.sensors.seismic_utils import (
    parse_seismic_message,
    save_seismic_data,
)


def list_serial_by_id():
    return sorted(glob.glob('/dev/serial/by-id/*'))


def detect_default_port():
    ports = list_serial_by_id()
    if ports:
        return ports[0]
    # Fallbacks comunes
    for p in ('/dev/ttyUSB0', '/dev/ttyACM0'):
        try:
            return p
        except Exception:
            pass
    return None


def current_interval_end(interval_minutes=1):
    now = datetime.now()
    minutes = (now.minute // interval_minutes) * interval_minutes
    interval_end = now.replace(minute=minutes, second=0, microsecond=0)
    fecha = interval_end.strftime('%Y-%m-%d')
    tiempo = interval_end.strftime('%H:%M:00')
    return fecha, tiempo


def main():
    parser = argparse.ArgumentParser(
        description='Lectura/parseo de datos sísmicos desde puerto serial.'
    )
    parser.add_argument('--port', '-p', type=str, default=None,
                        help='Ruta del puerto serial (por defecto autodetección en /dev/serial/by-id/*)')
    parser.add_argument('--baud', '-b', type=int, default=9600,
                        help='Baudios (por defecto 9600)')
    parser.add_argument('--interval-min', type=int, default=1,
                        help='Minutos por intervalo para timestamp (por defecto 1)')
    parser.add_argument('--save', action='store_true',
                        help='Si se indica, guarda cada lectura parseada en DTA usando save_seismic_data')
    parser.add_argument('--list', action='store_true',
                        help='Lista los puertos disponibles en /dev/serial/by-id y sale')
    parser.add_argument('--once', action='store_true',
                        help='Lee solo una línea válida (parseable) y sale')
    args = parser.parse_args()

    if args.list:
        ports = list_serial_by_id()
        if not ports:
            print('No se encontraron puertos en /dev/serial/by-id')
        else:
            print('Puertos disponibles:')
            for p in ports:
                print(' -', p)
        return

    port = args.port or detect_default_port()
    if port is None:
        print('[ERROR] No se pudo autodetectar puerto serial. Use --port para especificarlo o ejecute con --list para ver opciones.')
        sys.exit(1)

    print(f'Abrir puerto: {port} @ {args.baud} baud')

    try:
        with serial.Serial(port, args.baud, timeout=1) as ser:
            print('Leyendo datos. Ctrl+C para salir.')
            prev_time = None
            while True:
                raw = ser.readline()
                if not raw:
                    continue
                now = datetime.now()
                ts = now.strftime('%Y-%m-%d %H:%M:%S')
                text = raw.decode(errors='replace').strip()
                if not text:
                    continue

                # Delta entre líneas para diagnosticar frecuencia
                if prev_time is not None:
                    delta = (now - prev_time).total_seconds()
                    delta_str = f' (+{delta:.2f}s)'
                else:
                    delta_str = ''
                prev_time = now

                fecha, tiempo = current_interval_end(args.interval_min)
                parsed = parse_seismic_message(text, fecha, tiempo, voltage=None)

                print(f'[{ts}] RAW: {text}{delta_str}')
                if parsed is not None:
                    print('       PARSED:', json.dumps(parsed, ensure_ascii=False))
                    if args.save:
                        ok = save_seismic_data(text, fecha, tiempo)
                        print('       SAVE:  OK' if ok else '       SAVE:  ERROR')
                    if args.once:
                        break
                else:
                    print('       PARSED: <formato no reconocido>')
    except serial.SerialException as e:
        print(f'[ERROR] No se pudo abrir o leer el puerto serial: {e}')
        sys.exit(2)
    except KeyboardInterrupt:
        print('\nLectura finalizada por el usuario.')


if __name__ == '__main__':
    main()
