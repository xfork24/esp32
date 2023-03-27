import time

import ujson
from machine import Pin

from buzzer import create_buzzer
from connect import init_wifi
from display import create_oled
from led import create_rgb_led
from mqtt import MQTTClient
from sensor import read_aval

BUZZER_IO_PORT = 26  # 14/15-cannot_play, 12-cannot_init
SOIL_MOISTURE_SENSOR_AO_PORT = 34  # 13/15-cannot_work_after_wifi_inited
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
WATER_CTL_PORT = 32
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
wctl = Pin(WATER_CTL_PORT, Pin.OUT)

mqttc = None
wifi = None

auto_mode = True
timer_mode = True
sensor_mode = False
water_plants = False

timer_threshold = 86400
timer_last_watering_time = time.time()

sensor_low_threshold = 10
sensor_high_threshold = 50
sensor_value_threshold = 10
sensor_value_counter = 0


def build_ha_conn_topics(entity_name, entity_type='sensor'):
    config_topic = 'homeassistant/%s/HA/HA-%s-%s/config' % (entity_type, HA_DEVICE_NAME, entity_name)
    state_topic = 'HA-%s/%s/state' % (HA_DEVICE_NAME, entity_name)
    cmd_topic = 'HA-%s/%s/set' % (HA_DEVICE_NAME, entity_name)
    return config_topic, state_topic, cmd_topic


def build_ha_register_body(sensor_name, sensor_type, icon='mdi:thermometer'):
    return ujson.dumps({
        'unique_id': 'HA-%s-%s' % (HA_DEVICE_NAME, sensor_name),
        'name': sensor_type,
        'icon': icon,
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

HA_AUTO_MODE_CFG_TOPIC, HA_AUTO_MODE_STATE_TOPIC, HA_AUTO_MODE_CMD_TOPIC = build_ha_conn_topics('auto_mode', 'switch')
HA_AUTO_MODE_REGISTER_BODY = build_ha_register_body('auto_mode', 'auto_mode')

HA_TIMER_MODE_CFG_TOPIC, HA_TIMER_MODE_STATE_TOPIC, HA_TIMER_MODE_CMD_TOPIC = build_ha_conn_topics('timer_mode',
                                                                                                   'switch')
HA_TIMER_MODE_REGISTER_BODY = build_ha_register_body('timer_mode', 'timer_mode')

HA_SENSOR_MODE_CFG_TOPIC, HA_SENSOR_MODE_STATE_TOPIC, HA_SENSOR_MODE_CMD_TOPIC = build_ha_conn_topics('sensor_mode',
                                                                                                      'switch')
HA_SENSOR_MODE_REGISTER_BODY = build_ha_register_body('sensor_mode', 'sensor_mode')

HA_WATER_PLANTS_CFG_TOPIC, HA_WATER_PLANTS_STATE_TOPIC, HA_WATER_PLANTS_CMD_TOPIC = build_ha_conn_topics('water_plants',
                                                                                                         'switch')
HA_WATER_PLANTS_REGISTER_BODY = build_ha_register_body('water_plants', 'water_plants')


def server_to_esp32_cb(topic, msg):
    global auto_mode, timer_mode, sensor_mode, water_plants
    topic_str = topic.decode()
    msg_str = msg.decode()
    print(topic_str, msg_str)
    if topic_str == HA_SOIL_MOISTURE_CMD_TOPIC:
        oled.text(topic_str, 0, 0)
        oled.text(msg_str, 0, 16, True)
    elif topic_str == HA_WATER_PLANTS_CMD_TOPIC:
        if water_plants:
            return
        water_plants = True
        wctl.value(1)
        print('begin water plants')
        mqttc.publish(HA_WATER_PLANTS_STATE_TOPIC, 'ON')
        time.sleep(5)
        water_plants = False
        wctl.value(0)
        print('end water plants')
        mqttc.publish(HA_WATER_PLANTS_STATE_TOPIC, 'OFF')
    else:
        if topic_str == HA_AUTO_MODE_CMD_TOPIC:
            auto_mode = True if msg_str == 'ON' else False
            if auto_mode:
                if (timer_mode and sensor_mode) or not (timer_mode or sensor_mode):
                    timer_mode = True
                    sensor_mode = False
            else:
                timer_mode = False
                sensor_mode = False
        elif topic_str == HA_TIMER_MODE_CMD_TOPIC:
            timer_mode = True if msg_str == 'ON' else False
            if timer_mode:
                auto_mode = True
                sensor_mode = False
            else:
                auto_mode = timer_mode or sensor_mode
        elif topic_str == HA_SENSOR_MODE_CMD_TOPIC:
            sensor_mode = True if msg_str == 'ON' else False
            if sensor_mode:
                auto_mode = True
                timer_mode = False
            else:
                auto_mode = timer_mode or sensor_mode
        else:
            pass
        mqttc.publish(HA_AUTO_MODE_STATE_TOPIC, 'ON' if auto_mode else 'OFF')
        mqttc.publish(HA_TIMER_MODE_STATE_TOPIC, 'ON' if timer_mode else 'OFF')
        mqttc.publish(HA_SENSOR_MODE_STATE_TOPIC, 'ON' if sensor_mode else 'OFF')


def mqtt_connect():
    print('before create mqttc')
    client = MQTTClient(MQTT_SERVER_IP, MQTT_SERVER_PORT)
    client.set_message_callback(server_to_esp32_cb)
    print('before mqtt connect')
    client.connect(MQTT_ESP32_CLIENT_NAME, MQTT_SERVER_USER, MQTT_SERVER_PASSWD)
    time.sleep(0.5)
    print('after mqtt connect')
    client.subscribe(HA_SOIL_MOISTURE_CMD_TOPIC)
    client.subscribe(HA_AUTO_MODE_CMD_TOPIC)
    client.subscribe(HA_TIMER_MODE_CMD_TOPIC)
    client.subscribe(HA_SENSOR_MODE_CMD_TOPIC)
    client.subscribe(HA_WATER_PLANTS_CMD_TOPIC)
    return client


def init_rgb():
    rgb = create_rgb_led(RGB_R_PORT, RGB_G_PORT, RGB_B_PORT)
    return rgb


def init_buzz():
    print('before init buzz')
    buzz = create_buzzer(BUZZER_IO_PORT)
    return buzz


def init_oled():
    print('before init oled')
    oled = create_oled(OLED_WIDTH, OLED_HEIGHT,
                       OLED_RES_PORT, OLED_DC_PORT, OLED_CS_PORT, OLED_CLK_PORT, OLED_MOSI_PORT, OLED_MISO_PORT)
    return oled


def handle_watering():
    pass


def main():
    global mqttc, wifi, rgb, buzz, oled

    rgb = init_rgb()
    wifi = init_wifi(WIFI_ESSID, WIFI_PASSWD)
    buzz = init_buzz()
    oled = init_oled()

    mqttc = mqtt_connect()
    print('before mqtt publish')
    mqttc.publish(HA_SOIL_MOISTURE_CFG_TOPIC, HA_SOIL_MOISTURE_REGISTER_BODY)
    mqttc.publish(HA_AUTO_MODE_CFG_TOPIC, HA_AUTO_MODE_REGISTER_BODY)
    mqttc.publish(HA_TIMER_MODE_CFG_TOPIC, HA_TIMER_MODE_REGISTER_BODY)
    mqttc.publish(HA_SENSOR_MODE_CFG_TOPIC, HA_SENSOR_MODE_REGISTER_BODY)
    mqttc.publish(HA_WATER_PLANTS_CFG_TOPIC, HA_WATER_PLANTS_REGISTER_BODY)

    mqttc.publish(HA_AUTO_MODE_STATE_TOPIC, 'ON' if auto_mode else 'OFF')
    mqttc.publish(HA_TIMER_MODE_STATE_TOPIC, 'ON' if timer_mode else 'OFF')
    mqttc.publish(HA_SENSOR_MODE_STATE_TOPIC, 'ON' if sensor_mode else 'OFF')
    mqttc.publish(HA_WATER_PLANTS_STATE_TOPIC, 'ON' if sensor_mode else 'OFF')

    print('before loop')
    while True:
        print(read_aval(SOIL_MOISTURE_SENSOR_AO_PORT))
        mqttc.publish(HA_SOIL_MOISTURE_STATE_TOPIC, str(read_aval(SOIL_MOISTURE_SENSOR_AO_PORT)))
        handle_watering()
        time.sleep(1)


if __name__ == '__main__':
    main()
