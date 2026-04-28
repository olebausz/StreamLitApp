import subprocess
import sys


def run_on_pico(code: str, port: str = "auto", exec_timeout_s: float = 20.0):
    cmd = [sys.executable, "-m", "mpremote", "connect", port, "exec", code]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=exec_timeout_s)
    return proc.stdout.strip(), proc.stderr.strip()


LED_CODE = '''
from machine import Pin
from utime import sleep

sleep(0.01)
print("Hello, Pi Pico!")

try:
    led = Pin("LED", Pin.OUT)
except Exception:
    led = Pin(25, Pin.OUT)

for _ in range(20):
    led.toggle()
    sleep(0.5)
'''


def list_ports():
    cmd = [sys.executable, "-m", "mpremote", "connect", "list"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return proc.stdout.strip(), proc.stderr.strip()


def run(port: str = "COM3"):
    ports_out, ports_err = list_ports()
    out, err = run_on_pico(LED_CODE, port=port, exec_timeout_s=20)
    return {
        "ports": ports_out or "Keine Ports von mpremote erkannt.",
        "ports_error": ports_err,
        "stdout": out,
        "stderr": err,
    }


if __name__ == "__main__":
    result = run()
    print(result["ports"])
    if result["ports_error"]:
        print("PORT STDERR:\n", result["ports_error"])
    print("STDOUT:\n", result["stdout"])
    print("STDERR:\n", result["stderr"])
