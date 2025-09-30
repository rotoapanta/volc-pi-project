import lgpio
chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, 16)
lgpio.gpio_write(chip, 16, 1)  # Enciende el LED
input("Presiona Enter para apagar el LED...")
lgpio.gpio_write(chip, 16, 0)  # Apaga el LED
lgpio.gpiochip_close(chip)