COLOR_RESET = "\033[0m"
COLOR_OK = "\033[1;32m"      # Verde brillante
COLOR_FAIL = "\033[1;31m"    # Rojo brillante
COLOR_WARN = "\033[1;33m"    # Amarillo brillante
COLOR_INFO = "\033[1;36m"    # Cian brillante
COLOR_PENDING = "\033[1;37m" # Gris claro
COLOR_SEISMIC = "\033[1;33m" # Amarillo
COLOR_PLUVIOMETER = "\033[1;36m" # Cian
COLOR_GPS = "\033[1;35m" # Magenta
COLOR_BATTERY = "\033[1;32m" # Verde

def print_colored(msg):
    if msg.startswith("[ OK ]"):
        print(f"{COLOR_OK}{msg}{COLOR_RESET}")
    elif msg.startswith("[FAIL]"):
        print(f"{COLOR_FAIL}{msg}{COLOR_RESET}")
    elif msg.startswith("[WARN]"):
        print(f"{COLOR_WARN}{msg}{COLOR_RESET}")
    elif msg.startswith("[INFO]"):
        print(f"{COLOR_INFO}{msg}{COLOR_RESET}")
    elif msg.startswith("[....]"):
        print(f"{COLOR_PENDING}{msg}{COLOR_RESET}")
    elif msg.startswith("[SEISMIC]"):
        print(f"{COLOR_SEISMIC}{msg}{COLOR_RESET}")
    elif msg.startswith("[PLUVIOMETER]"):
        print(f"{COLOR_PLUVIOMETER}{msg}{COLOR_RESET}")
    elif msg.startswith("[GPS]"):
        print(f"{COLOR_GPS}{msg}{COLOR_RESET}")
    elif msg.startswith("[BATTERY]"):
        print(f"{COLOR_BATTERY}{msg}{COLOR_RESET}")
    else:
        print(msg)

def log_and_color(logger, msg):
    import datetime
    logger.info(msg)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    print_colored(f"{now} - INFO - {msg}")
