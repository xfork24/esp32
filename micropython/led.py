import time

from machine import Pin, PWM

rgb_inited = False
pwm_led_r = None
pwm_led_g = None
pwm_led_b = None


def rgb(r=255, g=255, b=255, r_port=14, g_port=12, b_port=13, freq=1000):
    global rgb_inited
    global pwm_led_r
    global pwm_led_g
    global pwm_led_b
    if not rgb_inited:
        rgb_inited = True
        led_r = Pin(r_port, Pin.OUT)
        led_g = Pin(g_port, Pin.OUT)
        led_b = Pin(b_port, Pin.OUT)
        pwm_led_r = PWM(led_r)
        pwm_led_g = PWM(led_g)
        pwm_led_b = PWM(led_b)
    pwm_led_r.freq(freq)
    pwm_led_r.duty(int(r / 255 * 1023))
    pwm_led_g.freq(freq)
    pwm_led_g.duty(int(g / 255 * 1023))
    pwm_led_b.freq(freq)
    pwm_led_b.duty(int(b / 255 * 1023))


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
