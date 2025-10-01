import lgpio
import time

GPIO_PIN = 5  # Cambia este valor si tu LED está en otro pin

try:
    chip = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(chip, GPIO_PIN)
    print(f"Encendiendo LED en GPIO {GPIO_PIN}...")
    lgpio.gpio_write(chip, GPIO_PIN, 1)
    time.sleep(3)
    print(f"Apagando LED en GPIO {GPIO_PIN}...")
    lgpio.gpio_write(chip, GPIO_PIN, 0)
    lgpio.gpiochip_close(chip)
    print("Prueba completada.")
except Exception as e:
    print(f"Error al probar el LED en GPIO {GPIO_PIN}: {e}")
