#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba: blinking para todos los GPIOs del Raspberry Pi 5 usando lgpio.

- Por defecto prueba los GPIOs del header en modo seguro (omite pines reservados: I2C0/1, SPI, UART).
- Puede incluir pines reservados con --include-reserved.
- Permite seleccionar un subconjunto con --only o excluir con --skip.

Requisitos:
  sudo apt install python3-lgpio

Uso:
  sudo python3 scripts/blink_all_gpio.py
  sudo python3 scripts/blink_all_gpio.py --include-reserved
  sudo python3 scripts/blink_all_gpio.py --only 5,6,16 --on 0.1 --off 0.1 --cycles 5

Notas importantes:
- Si algún GPIO está en uso por otro proceso/servicio (p.ej. I2C en 2/3, UART en 14/15, SPI en 7/8/9/10/11 o tu aplicación), la reclamación puede fallar.
- Ejecuta como root (sudo) para evitar problemas de permisos.
"""

import argparse
import time
import sys

try:
    import lgpio
except Exception as e:
    print("ERROR: No se pudo importar lgpio. Instala con: sudo apt install python3-lgpio", file=sys.stderr)
    raise

# GPIOs BCM presentes en el header de 40 pines del Raspberry Pi (0..27)
ALL_HEADER_BCM = [
    0, 1,                 # I2C0 EEPROM (HAT ID)
    2, 3,                 # I2C1 SDA/SCL
    4,
    5, 6,
    7, 8, 9, 10, 11,     # SPI0 (CE1, CE0, MISO, MOSI, SCLK)
    12, 13,               # PWM
    14, 15,               # UART (TXD, RXD)
    16,
    17, 18,
    19,                   # PCM/SPI1 (según uso)
    20, 21,               # SPI1/PCM (según uso)
    22, 23, 24, 25,
    26, 27,
]

# Pines reservados usuales para no tocarlos por defecto
RESERVED_DEFAULT = [0, 1, 2, 3, 7, 8, 9, 10, 11, 14, 15]


def parse_csv_ints(s: str):
    vals = []
    for part in s.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            vals.append(int(part))
        except ValueError:
            raise argparse.ArgumentTypeError(f"Valor no entero en lista: '{part}'")
    return vals


def main():
    p = argparse.ArgumentParser(description="Blink de todos los GPIOs (BCM) con lgpio")
    p.add_argument('--include-reserved', action='store_true', help='Incluir pines reservados (I2C, SPI, UART, EEPROM)')
    p.add_argument('--only', type=parse_csv_ints, help='Lista de GPIOs BCM a probar, separados por coma. Ej: 5,6,16')
    p.add_argument('--skip', type=parse_csv_ints, help='Lista de GPIOs BCM a omitir, separados por coma. Ej: 2,3')
    p.add_argument('--on', type=float, default=0.2, help='Tiempo encendido por ciclo (s)')
    p.add_argument('--off', type=float, default=0.2, help='Tiempo apagado por ciclo (s)')
    p.add_argument('--cycles', type=int, default=3, help='Número de ciclos de parpadeo por GPIO')
    p.add_argument('--chip', type=int, default=0, help='Índice de gpiochip (por defecto 0)')
    p.add_argument('--verbose', action='store_true', help='Salida detallada')
    p.add_argument('--dry-run', action='store_true', help='No modifica GPIOs, solo muestra qué haría')
    args = p.parse_args()

    if args.only:
        gpios = args.only
    else:
        gpios = list(ALL_HEADER_BCM)
        if not args.include_reserved:
            gpios = [g for g in gpios if g not in RESERVED_DEFAULT]
        if args.skip:
            to_skip = set(args.skip)
            gpios = [g for g in gpios if g not in to_skip]

    if not gpios:
        print("No hay GPIOs para probar. Revisa --only / --skip / --include-reserved.")
        return 0

    print("GPIOs a probar (BCM):", gpios)
    if args.dry_run:
        print("[DRY-RUN] No se realizarán cambios en los GPIOs.")
        return 0

    chip = None
    claimed = []
    try:
        chip = lgpio.gpiochip_open(args.chip)
    except Exception as e:
        print(f"ERROR: No se pudo abrir gpiochip{args.chip}: {e}", file=sys.stderr)
        return 1

    try:
        for gpio in gpios:
            try:
                # liberar si estaba en uso por este proceso
                try:
                    lgpio.gpio_free(chip, gpio)
                except Exception:
                    pass

                # reclamar como salida; nivel inicial en 0
                lgpio.gpio_claim_output(chip, gpio)
                claimed.append(gpio)
                if args.verbose:
                    print(f"GPIO {gpio}: reclamado como salida")

                for i in range(args.cycles):
                    if args.verbose:
                        print(f"GPIO {gpio}: ciclo {i+1}/{args.cycles} -> ON")
                    lgpio.gpio_write(chip, gpio, 1)
                    time.sleep(args.on)
                    if args.verbose:
                        print(f"GPIO {gpio}: ciclo {i+1}/{args.cycles} -> OFF")
                    lgpio.gpio_write(chip, gpio, 0)
                    time.sleep(args.off)

                # asegurar apagado
                lgpio.gpio_write(chip, gpio, 0)
                print(f"GPIO {gpio}: OK")
            except KeyboardInterrupt:
                print("Interrumpido por el usuario.")
                break
            except Exception as e:
                print(f"GPIO {gpio}: ERROR -> {e}")
                # intentar dejarlo en bajo si ya lo reclamamos
                try:
                    if gpio in claimed:
                        lgpio.gpio_write(chip, gpio, 0)
                except Exception:
                    pass
                # continuar con el siguiente
                continue
    finally:
        # liberar todos los que reclamamos
        for gpio in claimed:
            try:
                lgpio.gpio_write(chip, gpio, 0)
            except Exception:
                pass
            try:
                lgpio.gpio_free(chip, gpio)
            except Exception:
                pass
        try:
            if chip is not None:
                lgpio.gpiochip_close(chip)
        except Exception:
            pass

    print("Prueba completada.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
