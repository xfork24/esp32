import time

from machine import Pin, PWM

from config import ESP32_BOARD_BLUE_LED_PIN_PORT


def blink(pin=ESP32_BOARD_BLUE_LED_PIN_PORT, freq_ms=500, second=5):
    pin = Pin(pin, Pin.OUT)
    for i in range(int(second * 500 / freq_ms)):
        pin.value(1)
        time.sleep_ms(freq_ms)
        pin.value(0)
        time.sleep_ms(freq_ms)


def pwm(pin=ESP32_BOARD_BLUE_LED_PIN_PORT, freq=1000, second=11):
    led2 = PWM(Pin(pin))
    led2.freq(freq)

    for i in range(int(second * 0.48828125)):
        for j in range(0, 1024):
            led2.duty(j)
            time.sleep_ms(1)

        for j in range(1023, -1, -1):
            led2.duty(j)
            time.sleep_ms(1)
