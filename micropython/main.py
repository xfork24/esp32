from connect import wifi_connect
from umqtt import MQTTClient
from constant import *
from display import init_lcd
import time

lcd = init_lcd()

def sub_cb(topic, msg):
    print(topic, msg)
    info = msg.decode()
    lcd.lcd_clear()
    time.sleep(1)
    lcd.lcd_print(info, 0, 0)

def main():
    wifi_connect(WIFI_ESSID, WIFI_PASSWD)
    mqtt = MQTTClient(MQTT_ESP32_CLIENT_NAME, MQTT_SERVER_IP, MQTT_SERVER_PORT, MQTT_SERVER_USER, MQTT_SERVER_PASSWD)
    mqtt.set_callback(sub_cb)
    mqtt.connect()
    mqtt.subscribe(MQTT_ESP32_SUBSCRIBE_TOPIC)
    while True:
        mqtt.check_msg()
        time.sleep(1)


if __name__ == '__main__':
    main()
