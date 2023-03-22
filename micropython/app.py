from buzzer import play
from led import blink, pwm


def main():
    blink()
    pwm()
    play()


if __name__ == '__main__':
    main()
