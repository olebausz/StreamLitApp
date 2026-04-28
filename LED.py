import subprocess
import sys


DEFAULT_PORT = "COM3"


def run_on_pico(code: str, port: str = DEFAULT_PORT, exec_timeout_s: float = 5.0):
    cmd = [sys.executable, "-m", "mpremote", "connect", port, "exec", code]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=exec_timeout_s)
    return proc.stdout.strip(), proc.stderr.strip()


def led_code(enabled: bool) -> str:
    value = 1 if enabled else 0
    return f'''
from machine import Pin

try:
    led = Pin("LED", Pin.OUT)
except Exception:
    led = Pin(25, Pin.OUT)

led.value({value})
'''


def list_ports():
    cmd = [sys.executable, "-m", "mpremote", "connect", "list"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return proc.stdout.strip(), proc.stderr.strip()


def set_led(enabled: bool, port: str = DEFAULT_PORT):
    out, err = run_on_pico(led_code(enabled), port=port, exec_timeout_s=5)
    return {
        "stdout": out,
        "stderr": err,
    }


def port_check():
    ports_out, ports_err = list_ports()
    return {
        "ports": ports_out or "Keine Ports von mpremote erkannt.",
        "stderr": ports_err,
        "hint": "Damit alle Skripte funktionieren, muss der Raspberry Pi Pico auf COM3 angeschlossen sein.",
    }


if __name__ == "__main__":
    result = port_check()
    print(result["ports"])
    print(result["hint"])
    if result["stderr"]:
        print("STDERR:\n", result["stderr"])
