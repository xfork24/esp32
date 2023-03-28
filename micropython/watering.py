import time

import ujson
from machine import Pin, Timer, WDT

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
WATER_PERIOD = 5
WD_THRESHOLD = 30000

rgb = None
buzz = None
oled = None
wctl = Pin(WATER_CTL_PORT, Pin.OUT)

mqttc = None
wifi = None

auto_mode = True
timer_mode = True
sensor_mode = False
manual_status = False
water_status = False
auto_trigger = True

timer_threshold = 10
timer_last_watering_time = time.time()

sensor_low_threshold = 20
sensor_high_threshold = 50
sensor_value_count_threshold = 10
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

HA_WATER_STATUS_CFG_TOPIC, HA_WATER_STATUS_STATE_TOPIC, HA_WATER_STATUS_CMD_TOPIC = build_ha_conn_topics('water_status',
                                                                                                         'switch')
HA_WATER_STATUS_REGISTER_BODY = build_ha_register_body('water_status', 'water_status')


def switch_water_status(on=True, auto=True):
    global water_status, timer_last_watering_time, auto_trigger, sensor_value_counter
    if on and water_status and not auto:
        print('watering already in progress, ignore command')
        mqttc.publish(HA_WATER_PLANTS_STATE_TOPIC, 'OFF')
        return
    switch = 'ON' if on else 'OFF'
    print('%s %s water plants' % ('begin' if on else 'end', 'auto' if auto else 'manual'))
    auto_trigger = auto
    water_status = on
    wctl.value(1 if on else 0)
    mqttc.publish(HA_WATER_STATUS_STATE_TOPIC, switch)
    if not auto:
        mqttc.publish(HA_WATER_PLANTS_STATE_TOPIC, switch)
    timer_last_watering_time = time.time()
    sensor_value_counter = 0
    if on:
        tim0 = Timer(0)
        tim0.init(period=WATER_PERIOD * 1000, mode=Timer.ONE_SHOT, callback=watering_timer)


def watering_timer(t):
    print('in watering timer', t)
    switch_water_status(False, auto_trigger)


def server_to_esp32_cb(topic, msg):
    global auto_mode, timer_mode, sensor_mode, water_status
    topic_str = topic.decode()
    msg_str = msg.decode()
    print(topic_str, msg_str)
    if topic_str == HA_WATER_PLANTS_CMD_TOPIC:
        switch_water_status(True, False)
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
    time.sleep(5)
    print('after mqtt connect')
    client.subscribe(HA_AUTO_MODE_CMD_TOPIC)
    client.subscribe(HA_TIMER_MODE_CMD_TOPIC)
    client.subscribe(HA_SENSOR_MODE_CMD_TOPIC)
    client.subscribe(HA_WATER_PLANTS_CMD_TOPIC)
    return client


def init_rgb():
    c = create_rgb_led(RGB_R_PORT, RGB_G_PORT, RGB_B_PORT)
    return c


def init_buzz():
    print('before init buzz')
    c = create_buzzer(BUZZER_IO_PORT)
    return c


def init_oled():
    print('before init oled')
    c = create_oled(OLED_WIDTH, OLED_HEIGHT,
                    OLED_RES_PORT, OLED_DC_PORT, OLED_CS_PORT, OLED_CLK_PORT, OLED_MOSI_PORT, OLED_MISO_PORT)
    return c


def handle_auto_watering(soil_moisture):
    global sensor_value_counter, timer_last_watering_time, water_status
    if water_status:
        return
    if not auto_mode:
        sensor_value_counter = 0
        timer_last_watering_time = time.time()
        return
    if sensor_mode:
        if sensor_low_threshold < soil_moisture < sensor_high_threshold:
            sensor_value_counter = 0
        if soil_moisture < sensor_low_threshold:
            sensor_value_counter += 1
        if sensor_value_counter > sensor_value_count_threshold:
            switch_water_status(True, True)
    elif timer_mode:
        timestamp = time.time()
        if timestamp - timer_last_watering_time > timer_threshold:
            switch_water_status(True, True)
    else:
        pass


def main():
    global mqttc, wifi, rgb, buzz, oled

    wdt = WDT(timeout=WD_THRESHOLD)
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
    mqttc.publish(HA_WATER_STATUS_CFG_TOPIC, HA_WATER_STATUS_REGISTER_BODY)

    mqttc.publish(HA_AUTO_MODE_STATE_TOPIC, 'ON' if auto_mode else 'OFF')
    mqttc.publish(HA_TIMER_MODE_STATE_TOPIC, 'ON' if timer_mode else 'OFF')
    mqttc.publish(HA_SENSOR_MODE_STATE_TOPIC, 'ON' if sensor_mode else 'OFF')
    mqttc.publish(HA_WATER_PLANTS_STATE_TOPIC, 'ON' if manual_status else 'OFF')
    mqttc.publish(HA_WATER_STATUS_STATE_TOPIC, 'ON' if water_status else 'OFF')

    print('before loop')
    while True:
        print(read_aval(SOIL_MOISTURE_SENSOR_AO_PORT))
        soil_moisture = read_aval(SOIL_MOISTURE_SENSOR_AO_PORT)
        mqttc.publish(HA_SOIL_MOISTURE_STATE_TOPIC, str(soil_moisture))
        mqttc.publish(HA_WATER_STATUS_STATE_TOPIC, 'ON' if water_status else 'OFF')
        handle_auto_watering(soil_moisture)
        wdt.feed()
        time.sleep(1)


if __name__ == '__main__':
    main()
