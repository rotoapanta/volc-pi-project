import lgpio
import time

# Diccionario de LEDs y sus GPIOs según tu configuración
led_pins = {
    "ETH": 16,
    "WIFI": 27,
    "VOLTAGE": 6,
    "MEDIA": 25
}

try:
    chip = lgpio.gpiochip_open(0)
    for name, pin in led_pins.items():
        lgpio.gpio_claim_output(chip, pin)
        print(f"Encendiendo LED {name} (GPIO {pin})...")
        lgpio.gpio_write(chip, pin, 1)
        time.sleep(2)
        print(f"Apagando LED {name} (GPIO {pin})...")
        lgpio.gpio_write(chip, pin, 0)
    lgpio.gpiochip_close(chip)
    print("Prueba de LEDs completada.")
except Exception as e:
    print(f"Error al probar los LEDs: {e}")
