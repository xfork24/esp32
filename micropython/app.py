import time

from display import init_oled
from sensor import read_aval


def main():
    oled = init_oled()
    while True:
        oled.fill(0)
        oled.show()
        val = read_aval()
        oled.text(str(val), 0, 0)
        oled.show()
        time.sleep(0.5)


if __name__ == '__main__':
    main()
