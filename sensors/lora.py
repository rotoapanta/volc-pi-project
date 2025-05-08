# sensors/lora.py - Módulo placeholder para comunicación LoRa

class LoRaModule:
    def __init__(self):
        self.connected = False

    def initialize(self):
        print("[....] Inicializando módulo LoRa...")
        self.connected = True

    def status(self):
        return {"connected": self.connected}

    def send(self, message):
        if self.connected:
            print(f"[TX] Enviando por LoRa: {message}")
        else:
            print("[FAIL] Módulo LoRa no conectado")

    def receive(self):
        if self.connected:
            return "Mensaje simulado recibido por LoRa"
        return None