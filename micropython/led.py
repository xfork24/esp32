import time

from machine import Pin, PWM


def blink(port=2, freq=2, period=5):
    led = Pin(port, Pin.OUT)
    for i in range(int(period * freq / 2)):  # period / (1/freq * 2)
        led.value(1)
        time.sleep_ms(int(1000 / freq))
        led.value(0)
        time.sleep_ms(int(1000 / freq))


def pwm(port=2, freq=1000, period=11):
    led = PWM(Pin(port))
    led.freq(freq)

    for i in range(int(period * freq / 2048)):  # period / (1024 * 1/freq * 2)
        for j in range(0, 1024):
            led.duty(j)
            time.sleep_ms(int(1000 / freq))

        for j in range(1023, -1, -1):
            led.duty(j)
            time.sleep_ms(int(1000 / freq))
