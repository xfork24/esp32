import random
import time

from led import rgb


def main():
    random.seed(time.ctime())
    for i in range(5):
        rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        time.sleep(1)
    rgb(0, 0, 0)


if __name__ == '__main__':
    main()
