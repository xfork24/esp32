import time

import network


def wifi_connect(essid, passwd):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try_count = 0
    while not wlan.isconnected():
        try_count += 1
        print('connecting to wifi network ... try {0}'.format(try_count))
        wlan.connect(essid, passwd)
        time.sleep(1)
    print('wifi network connected, configuration: ', wlan.ifconfig())
