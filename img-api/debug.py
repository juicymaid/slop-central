# log.py
import sys
import time

# ANSI colors
COLORS = {
    "INFO": "\033[96m",     # cyan
    "WARNING": "\033[93m",  # yellow
    "ERROR": "\033[91m",    # red
    "RESET": "\033[0m"
}

def log(level: str, message: str):
    color = COLORS.get(level, "")
    reset = COLORS["RESET"]
    timestamp = time.strftime("%H:%M:%S")

    # Format like: INFO     Started server process [12345]
    sys.stdout.write(f"{color}{level:<8}{reset} {message}\n")

