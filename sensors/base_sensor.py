class BaseSensor:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger

    def acquire(self):
        """Adquisición de datos crudos"""
        raise NotImplementedError

    def process(self, raw_data):
        """Procesamiento y validación de datos"""
        raise NotImplementedError

    def save(self, processed_data):
        """Guardado de datos en archivo propio"""
        raise NotImplementedError

    def send(self, processed_data):
        """Envío de datos (opcional)"""
        pass
