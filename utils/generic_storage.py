class GenericDataStorage:
    def __init__(self, station_name, identifier, model, serial_number, tipo):
        self.station_name = station_name
        self.identifier = identifier
        self.model = model
        self.serial_number = serial_number
        self.tipo = tipo
        self.data_accumulator = {}
        self.acquisition_interval = 1

    def accumulate(self, data, acquisition_interval=1):
        # Acumula datos en memoria (puedes implementar guardado real después)
        key = data.get("FECHA", "unknown")
        if key not in self.data_accumulator:
            self.data_accumulator[key] = []
        self.data_accumulator[key].append(data)
        # Simula que guarda en un archivo y retorna la ruta
        filename = f"{self.tipo}_{key}.json"
        return [filename]
