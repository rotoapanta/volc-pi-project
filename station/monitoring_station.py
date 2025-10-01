class MonitoringStation:
    def __init__(self, managers, logger, leds=None):
        self.managers = managers  # Lista de managers (RainManager, SeismicManager, etc.)
        self.logger = logger
        self.leds = leds
        if self.leds:
            self.leds.heartbeat()

    def start_all(self):
        import threading
        for manager in self.managers:
            if hasattr(manager, 'run'):
                threading.Thread(target=manager.run, daemon=True).start()
            elif hasattr(manager, 'start'):
                threading.Thread(target=manager.start, daemon=True).start()
            else:
                self.logger.warning(f"[MONITORING] Manager {manager.__class__.__name__} no tiene método 'run' ni 'start'.")
        self.logger.info("[MONITORING] All managers started.")

    def run_forever(self):
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.warning("[MONITORING] Manual interruption received. Stopping station.")
