#!/usr/bin/env python3
import json, time, random, argparse, serial, math
from datetime import datetime, timedelta
from serial.tools import list_ports

# ------------- Serial / LoRa ----------
DEFAULT_BAUD = 115200
ACK_TIMEOUT = 1.5    # seg
RETRIES     = 2
MAX_BYTES   = 220    # tamaño recomendado por paquete

def find_lora_port(vid="1a86", pid="55d3", fallback="/dev/ttyACM0"):
    for p in list_ports.comports():
        if p.vid and p.pid and f"{p.vid:04x}" == vid and f"{p.pid:04x}" == pid:
            return p.device
    return fallback

# ------------- Generadores de datos -------------
def rnd_uniform(c, w):  # centro, amplitud
    return c + random.uniform(-w, w)

def gen_rga_read(base_ts, lat, lon, alt, nivel_base=0.0, bat=12.5):
    """Una lectura RGA (telemetría) con pequeñas variaciones."""
    ts = base_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    lectura = {
        "ts": ts,
        "lat": round(rnd_uniform(lat, 0.00002), 6),
        "lon": round(rnd_uniform(lon, 0.00002), 6),
        "alt": round(alt + rnd_uniform(0, 0.5), 1),
        "mm":  round(max(0.0, nivel_base + rnd_uniform(0.0, 0.5)), 3),
        "bat": round(max(9.0, bat - random.uniform(0, 0.002)), 2),
    }
    return lectura

def gen_sis_read(base_ts, lat, lon, alt, bat=12.5):
    """Una lectura sísmica; ALERTA aleatoria baja, y 3 canales 'filtros'."""
    ts = base_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    alerta = random.random() < 0.02  # 2% de probabilidad
    # Usa strings de 4 dígitos como indicaste, variando suavemente
    p_banda  = f"{random.randint(0, 99):02d}{random.randint(0, 99):02d}"
    p_bajo   = f"{random.randint(0, 99):02d}{random.randint(0, 99):02d}"
    p_alto   = f"{random.randint(0, 99):02d}{random.randint(0, 99):02d}"
    lectura = {
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
    return lectura

# ------------- Envío con ACK -------------
def send_with_ack(ser, pkt_str, pkt_id):
    frame = (pkt_str + "\r\n").encode("utf-8")  # CRLF para modo transparente
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

# ------------- Main -------------
def main():
    ap = argparse.ArgumentParser(description="LoRa random sender (RGA/SIS) con ACK")
    ap.add_argument("--tipo", choices=["RGA","SIS"], required=True, help="Tipo de datos")
    ap.add_argument("--nombre", default="REVS2")
    ap.add_argument("--ident", type=int, default=1)
    ap.add_argument("--lat", type=float, default=-0.212183)
    ap.add_argument("--lon", type=float, default=-78.491557)
    ap.add_argument("--alt", type=float, default=2814.1)

    ap.add_argument("--period", type=int, help="Segundos entre paquetes (RGA default 60, SIS default 15)")
    ap.add_argument("--batch", type=int, default=5, help="# lecturas por paquete (solo RGA)")
    ap.add_argument("--port", default=find_lora_port(), help="Puerto serial (ej. /dev/ttyACM0)")
    ap.add_argument("--baud", type=int, default=DEFAULT_BAUD)

    args = ap.parse_args()

    period = args.period if args.period else (60 if args.tipo=="RGA" else 15)
    port   = args.port
    baud   = args.baud

    print(f"[INFO] Tipo={args.tipo} Nombre={args.nombre} ID={args.ident}")
    print(f"[INFO] Puerto {port} @ {baud}  period={period}s  batch={args.batch if args.tipo=='RGA' else 1}")

    ser = serial.Serial(port, baud, timeout=ACK_TIMEOUT)
    pkt_id = 1
    now = datetime.utcnow()

    try:
        while True:
            if args.tipo == "RGA":
                # Encabezado compacto
                header = {"t":"RGA","n":args.nombre,"id":args.ident}
                # Genera 'batch' lecturas con timestamps a 1 min entre sí
                reads = []
                for i in range(args.batch):
                    ts_i = now + timedelta(seconds=i*60)
                    reads.append(gen_rga_read(ts_i, args.lat, args.lon, args.alt))
                now += timedelta(seconds=period)

                pkt = {"id": pkt_id, "seq": pkt_id, "h": header, "r": reads}
                pkt_str = json.dumps(pkt, separators=(",",":"))
                if len(pkt_str) > MAX_BYTES:
                    print(f"[WARN] Paquete grande ({len(pkt_str)}B) → baja --batch o reduce decimales.")
                ok = send_with_ack(ser, pkt_str, pkt_id)

            else:  # SIS
                header = {"t":"SIS","n":args.nombre,"id":args.ident}
                read = gen_sis_read(now, args.lat, args.lon, args.alt)
                now += timedelta(seconds=period)

                pkt = {"id": pkt_id, "seq": pkt_id, "h": header, "r":[read]}
                pkt_str = json.dumps(pkt, separators=(",",":"))
                ok = send_with_ack(ser, pkt_str, pkt_id)

            if not ok:
                print(f"[WARN] sin ACK para id={pkt_id}")

            pkt_id = (pkt_id + 1) % 100000
            time.sleep(period)

    except KeyboardInterrupt:
        print("\n[EXIT] Detenido por usuario.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
