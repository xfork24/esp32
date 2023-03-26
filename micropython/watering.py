import time

import ujson

from buzzer import create_buzzer
from connect import init_wifi
from display import create_oled
from led import create_rgb_led
from sensor import read_aval
from umqtt import MQTTClient

BUZZER_IO_PORT = 26  # 14/15-cannot_play, 12-cannot_init
SOIL_MOISTURE_SENSOR_AO_PORT = 13
RGB_R_PORT = 5
RGB_G_PORT = 4
RGB_B_PORT = 27
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_RES_PORT = 21
OLED_DC_PORT = 22
OLED_CS_PORT = 23
OLED_CLK_PORT = 18
OLED_MOSI_PORT = 19
OLED_MISO_PORT = 15
WIFI_ESSID = 'QQ2022'
WIFI_PASSWD = 'qqdataproduct'
MQTT_SERVER_IP = '175.178.162.201'
MQTT_SERVER_PORT = 1883
MQTT_SERVER_USER = 'admin'
MQTT_SERVER_PASSWD = '%uSIc849'
MQTT_ESP32_CLIENT_NAME = 'esp32_garden_helper_mqttc'
HA_DEVICE_NAME = 'esp32_garden_helper'
HA_DEVICE_MANUFACTURER = 'xfork.tech'
HA_DEVICE_MODEL = 'HA'
HA_DEVICE_SW_VERSION = '1.0'

rgb = None
buzz = None
oled = None

mqttc = None
wifi = None


def build_ha_conn_topics(sensor_name):
    config_topic = 'homeassistant/sensor/HA/HA-%s-%s/config' % (HA_DEVICE_NAME, sensor_name)
    state_topic = 'HA-%s/%s/state' % (HA_DEVICE_NAME, sensor_name)
    cmd_topic = 'HA-%s/%s/set' % (HA_DEVICE_NAME, sensor_name)
    return config_topic.encode(), state_topic.encode(), cmd_topic.encode()


def build_ha_register_body(sensor_name, sensor_type):
    return ujson.dumps({
        'unique_id': 'HA-%s-%s' % (HA_DEVICE_NAME, sensor_name),
        'name': sensor_type,
        'icon': 'mdi:thermometer',
        'state_topic': 'HA-%s/%s/state' % (HA_DEVICE_NAME, sensor_name),
        'json_attributes_topic': 'HA-%s/%s/attributes' % (HA_DEVICE_NAME, sensor_name),
        'command_topic': 'HA-%s/%s/set' % (HA_DEVICE_NAME, sensor_name),
        'device': {
            'identifiers': HA_DEVICE_NAME,
            'manufacturer': HA_DEVICE_MANUFACTURER,
            'model': HA_DEVICE_MODEL,
            'name': HA_DEVICE_NAME,
            'sw_version': HA_DEVICE_SW_VERSION
        }
    })


HA_SOIL_MOISTURE_CFG_TOPIC, HA_SOIL_MOISTURE_STATE_TOPIC, HA_SOIL_MOISTURE_CMD_TOPIC = build_ha_conn_topics(
    'soil_moisture')
HA_SOIL_MOISTURE_REGISTER_BODY = build_ha_register_body('soil_moisture', 'soil_moisture')


def server_to_esp32_cb(topic, msg):
    if topic.decode() == HA_SOIL_MOISTURE_CMD_TOPIC:
        oled.text(topic.decode, 0, 0)
        oled.text(msg, 0, 16, True)


def mqtt_connect():
    global mqttc
    print('before create mqttc')
    mqttc = MQTTClient(MQTT_ESP32_CLIENT_NAME,
                       MQTT_SERVER_IP, MQTT_SERVER_PORT,
                       MQTT_SERVER_USER, MQTT_SERVER_PASSWD)
    mqttc.set_callback(server_to_esp32_cb)
    print('before mqtt connect')
    mqttc.connect()
    print('after mqtt connect')
    mqttc.subscribe(HA_SOIL_MOISTURE_CMD_TOPIC)
    return mqttc


def init_rgb():
    global rgb
    if rgb is None:
        rgb = create_rgb_led(RGB_R_PORT, RGB_G_PORT, RGB_B_PORT)
    return rgb


def init_peripherals():
    global buzz, oled
    print('before init buzz')
    if buzz is None:
        buzz = create_buzzer(BUZZER_IO_PORT)
    print('before init oled')
    if oled is None:
        oled = create_oled(OLED_WIDTH, OLED_HEIGHT,
                           OLED_RES_PORT, OLED_DC_PORT, OLED_CS_PORT, OLED_CLK_PORT, OLED_MOSI_PORT, OLED_MISO_PORT)
    return buzz, oled


def main():
    global mqttc, wifi

    init_rgb()
    wifi = init_wifi(WIFI_ESSID, WIFI_PASSWD)
    init_peripherals()

    mqttc = mqtt_connect()
    mqttc.publish(HA_SOIL_MOISTURE_CFG_TOPIC, HA_SOIL_MOISTURE_REGISTER_BODY)

    print('before loop')
    while True:
        print(read_aval(SOIL_MOISTURE_SENSOR_AO_PORT))
        mqttc.publish(HA_SOIL_MOISTURE_STATE_TOPIC, read_aval(SOIL_MOISTURE_SENSOR_AO_PORT))
        time.sleep(1)


if __name__ == '__main__':
    main()
