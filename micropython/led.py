import time

from machine import Pin, PWM


def blink(port=2, freq_ms=500, second=5):
    led = Pin(port, Pin.OUT)
    for i in range(int(second * 500 / freq_ms)):
        led.value(1)
        time.sleep_ms(freq_ms)
        led.value(0)
        time.sleep_ms(freq_ms)


def pwm(port=2, freq=1000, second=11):
    led = PWM(Pin(port))
    led.freq(freq)

    for i in range(int(second * 0.48828125)):
        for j in range(0, 1024):
            led.duty(j)
            time.sleep_ms(1)

        for j in range(1023, -1, -1):
            led.duty(j)
            time.sleep_ms(1)
