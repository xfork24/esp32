import time

import machine


def blink(pin, second):
    pin = machine.Pin(pin, machine.Pin.OUT)
    for i in range(second):
        pin.value(1)
        time.sleep(1)
        pin.value(0)
        time.sleep(1)
