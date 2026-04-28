from machine import ADC, Pin
from onewire import OneWire
from ds18x20 import DS18X20
import time


ow = OneWire(Pin(22))
ds = DS18X20(ow)
internal_sensor = ADC(4)
devices = []


def read_internal_temperature():
    voltage = internal_sensor.read_u16() * 3.3 / 65535
    return 27 - (voltage - 0.706) / 0.001721

while True:
    if not devices:
        devices = ds.scan()
        if not devices:
            print("INFO: Kein DS18B20 Sensor gefunden. Pin, GND, 3V3 und Pull-up pruefen.")
            time.sleep_ms(500)
            continue

    try:
        ds.convert_temp()
    except Exception as exc:
        devices = []
        print("ERROR: OneWire Bus antwortet nicht:", exc)
        time.sleep_ms(500)
        continue

    time.sleep_ms(750)

    for dev in devices:
        try:
            temp = ds.read_temp(dev)
        except Exception as exc:
            devices = []
            print("ERROR: Temperatur konnte nicht gelesen werden:", exc)
            break

        internal_temp = read_internal_temperature()
        print(f"{temp},{internal_temp}")
