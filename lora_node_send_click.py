#!/usr/bin/env python3
import json, time, random, serial, math, click
from datetime import datetime, timedelta
from serial.tools import list_ports

DEFAULT_BAUD = 115200
ACK_TIMEOUT = 1.5
RETRIES = 2
MAX_BYTES = 220

# ---------- Buscar puerto LoRa ----------
def find_lora_port(vid="1a86", pid="55d3", fallback="/dev/ttyACM0"):
    for p in list_ports.comports():
        if p.vid and p.pid and f"{p.vid:04x}" == vid and f"{p.pid:04x}" == pid:
            return p.device
    return fallback

# ---------- Generadores ----------
def rnd_uniform(c, w):
    return c + random.uniform(-w, w)

def gen_rga_read(base_ts, lat, lon, alt, nivel_base=0.0, bat=12.5):
    ts = base_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "ts": ts,
        "lat": round(rnd_uniform(lat, 0.00002), 6),
        "lon": round(rnd_uniform(lon, 0.00002), 6),
        "alt": round(alt + rnd_uniform(0, 0.5), 1),
        "mm":  round(max(0.0, nivel_base + rnd_uniform(0.0, 0.5)), 3),
        "bat": round(max(9.0, bat - random.uniform(0, 0.002)), 2),
    }

def gen_sis_read(base_ts, lat, lon, alt, bat=12.5):
    ts = base_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    alerta = random.random() < 0.02
    p_banda = f"{random.randint(0, 99):02d}{random.randint(0, 99):02d}"
    p_bajo  = f"{random.randint(0, 99):02d}{random.randint(0, 99):02d}"
    p_alto  = f"{random.randint(0, 99):02d}{random.randint(0, 99):02d}"
    return {
        "ts": ts,
        "lat": round(rnd_uniform(lat, 0.00002), 6),
        "lon": round(rnd_uniform(lon, 0.00002), 6),
        "alt": round(alt + rnd_uniform(0, 0.5), 1),
        "alert": alerta,
        "pb": p_banda,
        "pl": p_bajo,
        "pa": p_alto,
        "bat": round(max(9.0, bat - random.uniform(0, 0.002)), 2),
    }

# ---------- Envío con ACK ----------
def send_with_ack(ser, pkt_str, pkt_id):
    frame = (pkt_str + "\r\n").encode("utf-8")
    for attempt in range(RETRIES + 1):
        ser.write(frame); ser.flush()
        print(f"[TX] id={pkt_id} try={attempt} {len(frame)}B")
        rx = ser.readline().decode(errors="ignore").strip()
        if rx == f"OK:{pkt_id}":
            print(f"[ACK] {rx}")
            return True
        if rx:
            print(f"[WAIT] {rx}")
    return False

# ---------- CLI principal ----------
@click.command()
@click.option("--tipo", type=click.Choice(["RGA", "SIS"], case_sensitive=False), required=True, help="Tipo de datos")
@click.option("--nombre", default="REVS2", show_default=True, help="Nombre del nodo")
@click.option("--ident", type=int, default=1, show_default=True, help="Identificador único")
@click.option("--lat", type=float, default=-0.212183, show_default=True)
@click.option("--lon", type=float, default=-78.491557, show_default=True)
@click.option("--alt", type=float, default=2814.1, show_default=True)
@click.option("--period", type=int, default=0, help="Segundos entre paquetes (RGA=60, SIS=15 por defecto)")
@click.option("--batch", type=int, default=5, show_default=True, help="Número de lecturas por paquete (solo RGA)")
@click.option("--port", default=find_lora_port(), show_default=True, help="Puerto serial (ej. /dev/ttyACM0)")
@click.option("--baud", type=int, default=DEFAULT_BAUD, show_default=True)
def main(tipo, nombre, ident, lat, lon, alt, period, batch, port, baud):
    """Envia datos aleatorios (RGA o SIS) por LoRa con confirmación (ACK)."""
    period = period or (60 if tipo == "RGA" else 15)
    print(f"[INFO] Tipo={tipo}  Nodo={nombre}  ID={ident}")
    print(f"[INFO] Puerto {port} @ {baud} period={period}s batch={batch if tipo=='RGA' else 1}")

    ser = serial.Serial(port, baud, timeout=ACK_TIMEOUT)
    pkt_id = 1
    now = datetime.utcnow()

    try:
        while True:
            if tipo == "RGA":
                header = {"t": "RGA", "n": nombre, "id": ident}
                reads = [gen_rga_read(now + timedelta(seconds=i*60), lat, lon, alt) for i in range(batch)]
                pkt = {"id": pkt_id, "seq": pkt_id, "h": header, "r": reads}
            else:
                header = {"t": "SIS", "n": nombre, "id": ident}
                reads = [gen_sis_read(now, lat, lon, alt)]
                pkt = {"id": pkt_id, "seq": pkt_id, "h": header, "r": reads}

            pkt_str = json.dumps(pkt, separators=(",", ":"))
            if len(pkt_str) > MAX_BYTES:
                print(f"[WARN] Paquete grande ({len(pkt_str)}B) → baja --batch o reduce decimales.")
            ok = send_with_ack(ser, pkt_str, pkt_id)
            if not ok:
                print(f"[WARN] sin ACK para id={pkt_id}")

            pkt_id = (pkt_id + 1) % 100000
            now += timedelta(seconds=period)
            time.sleep(period)

    except KeyboardInterrupt:
        print("\n[EXIT] Detenido por usuario.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
