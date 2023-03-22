import time

from config import *
from connect import wifi_connect
from display import init_lcd
from display import init_oled
from qr import QRCode
from umqtt import MQTTClient

lcd = init_lcd()


def sub_cb(topic, msg):
    print(topic, msg)
    info = msg.decode()
    lcd.lcd_clear()
    time.sleep(1)
    lcd.lcd_print(info, 0, 0)


def main1():
    wifi_connect(WIFI_ESSID, WIFI_PASSWD)
    mqtt = MQTTClient(MQTT_ESP32_CLIENT_NAME, MQTT_SERVER_IP, MQTT_SERVER_PORT, MQTT_SERVER_USER, MQTT_SERVER_PASSWD)
    mqtt.set_callback(sub_cb)
    mqtt.connect()
    mqtt.subscribe(MQTT_ESP32_SUBSCRIBE_TOPIC)
    count = 0
    while True:
        count += 1
        if count % 10 == 0:
            print('checking mqtt message, count = {0}, will try connect again'.format(count))
            try:
                mqtt.disconnect()
            except Exception as e:
                print(e)
            mqtt.connect()
            mqtt.subscribe(MQTT_ESP32_SUBSCRIBE_TOPIC)
        mqtt.check_msg()
        time.sleep(1)


def main2():
    qr = QRCode(border=2)
    qr.add_data('http://175.178.162.201:18083/')
    matrix = qr.get_matrix()

    row_len = len(matrix)
    col_len = len(matrix[0])

    scale_rate = 1
    oled = init_oled()

    for x in range(row_len * scale_rate):
        for y in range(col_len * scale_rate):
            if matrix[x // scale_rate][y // scale_rate]:
                oled.pixel(x, y + 16, 0xffff)
            y += 1
        x += 1
    oled.show()
