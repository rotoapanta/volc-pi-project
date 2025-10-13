#!/usr/bin/env python3
import time
import json
from datetime import datetime
import serial
from serial.tools import list_ports

# Busca automáticamente el puerto por VID:PID (QinHeng 1a86:55d3)
def find_lora_port(vid="1a86", pid="55d3"):
    for p in list_ports.comports():
        if p.vid and p.pid and f"{p.vid:04x}" == vid and f"{p.pid:04x}" == pid:
            return p.device
    return "/dev/ttyUSB0"  # fallback típico

PORT = find_lora_port()
BAUD = 115200

def open_serial():
    return serial.Serial(PORT, BAUD, timeout=1)

def send_line(ser, text: str):
    # En modo transparente basta con enviar una línea terminada en CRLF
    payload = (text + "\r\n").encode("utf-8")
    ser.write(payload)
    ser.flush()

def main():
    print(f"[INFO] Usando puerto {PORT} @ {BAUD} bps (modo transparente)")
    ser = None
    while True:
        try:
            if ser is None or not ser.is_open:
                ser = open_serial()
                print("[OK] Puerto abierto")

            # EJEMPLO de payload corto (<= 240 bytes recomendado)
            data = {
                "node": "RPI5-A",
                "ts": datetime.utcnow().isoformat(timespec="seconds")+"Z",
                "temp": 22.8,
                "bat": 3.98,
                "msg": "hola-dtu"
            }
            text = json.dumps(data, separators=(",", ":"))
            send_line(ser, text)
            print(f"[TX] {text}")

            # (Opcional) intenta leer respuesta si el otro lado eco/contesta
            rx = ser.readline().decode(errors="ignore").strip()
            if rx:
                print(f"[RX] {rx}")

            time.sleep(2)  # intervalo de envío
        except serial.SerialException as e:
            print(f"[WARN] Serial error: {e}. Reintentando en 3s…")
            try:
                if ser:
                    ser.close()
            except:
                pass
            ser = None
            time.sleep(3)
        except KeyboardInterrupt:
            break

    if ser and ser.is_open:
        ser.close()

if __name__ == "__main__":
    main()
