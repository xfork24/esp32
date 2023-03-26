from machine import Pin, ADC


def read_dval(pin=34):
    sensor = Pin(pin, Pin.IN)
    return sensor.value()


def read_aval(pin=34):
    sensor = ADC(Pin(pin))
    sensor.atten(ADC.ATTN_11DB)
    return 100 - sensor.read() / 40.95
