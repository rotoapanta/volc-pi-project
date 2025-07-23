import lgpio
import time

led_pins = [5, 6, 16, 22, 24, 25, 26]
h = lgpio.gpiochip_open(0)

for pin in led_pins:
    try:
        lgpio.gpio_claim_output(h, pin)
        print(f"[OK] GPIO {pin} listo.")
    except lgpio.error as e:
        print(f"[FAIL] GPIO {pin} ocupado: {e}")

# Parpadeo solo en los disponibles
for _ in range(15):
    for pin in led_pins:
        try:
            lgpio.gpio_write(h, pin, 1)
        except: continue
    time.sleep(0.3)
    for pin in led_pins:
        try:
            lgpio.gpio_write(h, pin, 0)
        except: continue
    time.sleep(0.3)

lgpio.gpiochip_close(h)
