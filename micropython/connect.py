import time

import network

wlan = None


def init_wifi(essid, passwd):
    global wlan
    if wlan is None:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        try_count = 0
        while not wlan.isconnected():
            try_count += 1
            print('connecting to wifi network ... try {0}'.format(try_count))
            try:
                wlan.connect(essid, passwd)
            except Exception as e:
                print(e)
            time.sleep(3)
    print('wifi network connected, configuration: ', wlan.ifconfig())
    return wlan
