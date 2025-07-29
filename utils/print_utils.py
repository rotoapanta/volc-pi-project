# utils/print_utils.py

COLOR_RESET = "\033[0m"
COLOR_OK = "\033[1;32m"      # Verde brillante
COLOR_FAIL = "\033[1;31m"    # Rojo brillante
COLOR_WARN = "\033[1;33m"    # Amarillo brillante
COLOR_INFO = "\033[1;36m"    # Cian brillante
COLOR_PENDING = "\033[1;37m" # Gris claro
COLOR_ERROR = "\033[1;41m"   # Fondo rojo para [ERROR] si se desea

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
    elif msg.startswith("[ERROR]"):
        print(f"{COLOR_FAIL}{msg}{COLOR_RESET}")
    else:
        print(msg)
