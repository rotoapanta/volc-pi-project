import lgpio
import time

PIN = 17
chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(chip, PIN)

print(f"Monitoreando GPIO{PIN}. Cambia el estado físico (puentea a GND/VCC o acciona el pluviómetro). Ctrl+C para salir.")

last_state = lgpio.gpio_read(chip, PIN)
print(f"Estado inicial: {last_state}")

try:
    while True:
        state = lgpio.gpio_read(chip, PIN)
        if state != last_state:
            print(f"[TEST] Cambio detectado en GPIO{PIN}: {last_state} -> {state} a {time.time()}")
            last_state = state
        time.sleep(0.001)
except KeyboardInterrupt:
    print("Test terminado.")
finally:
    lgpio.gpiochip_close(chip)
