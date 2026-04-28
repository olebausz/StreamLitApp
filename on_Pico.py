from machine import Pin
from onewire import OneWire
from ds18x20 import DS18X20
import time

ow = OneWire(Pin(22))
ds = DS18X20(ow)

devices = ds.scan()

while True:
    ds.convert_temp()
    time.sleep_ms(750)

    for dev in devices:
        temp = ds.read_temp(dev)
        print(temp)  # ❗ NUR ZAHL

    time.sleep(2)