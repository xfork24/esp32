import time

from machine import Pin, PWM

rgb = None


class _RgbLed:
    def __init__(self, r_port, g_port, b_port, freq):
        self.pwm_led_r = PWM(Pin(r_port, Pin.OUT))
        self.pwm_led_g = PWM(Pin(g_port, Pin.OUT))
        self.pwm_led_b = PWM(Pin(b_port, Pin.OUT))
        self.freq = freq
        self.show(0, 0, 0)

    def show(self, r, g, b):
        self.pwm_led_r.freq(self.freq)
        self.pwm_led_r.duty(int(r / 255 * 1023))
        self.pwm_led_g.freq(self.freq)
        self.pwm_led_g.duty(int(g / 255 * 1023))
        self.pwm_led_b.freq(self.freq)
        self.pwm_led_b.duty(int(b / 255 * 1023))


def create_rgb_led(r_port=5, g_port=4, b_port=27, freq=1000):
    global rgb
    if rgb is None:
        rgb = _RgbLed(r_port, g_port, b_port, freq)
    return rgb


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
