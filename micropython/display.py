from lcd2004 import LCD
from ssd1306 import SSD1306_SPI
from machine import Pin, SoftSPI
from time import sleep

def init_lcd(addr=39, scl=12, sda=13, backlight=False):
    lcd = LCD(addr, scl, sda)
    lcd.lcd_backlight(backlight)
    return lcd

def clean_lcd(lcd):
    lcd.lcd_clear()
    lcd.lcd_backlight(False)

def init_oled(width=128, height=64, res=21, dc=22, cs=23, sck=18, mosi=19, miso=15):
    spi = SoftSPI(baudrate=500000, polarity=1, phase=0, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
    res_pin = Pin(res)
    dc_pin = Pin(dc)
    cs_pin = Pin(cs)
    oled = SSD1306_SPI(width, height, spi, dc_pin, res_pin, cs_pin)
    oled.fill(0)
    return oled

def clean_oled(oled):
    oled.fill(0)
    oled.show()

def display_msg_in_lcd_and_oled(show_time=5):
    lcd = init_lcd()
    lcd.lcd_print('Happy Wife,', 0, 0)
    lcd.lcd_print('Happy Life!', 1, 0)

    oled = init_oled()
    oled.text('Wife is always', 0, 0)
    oled.text('RIGHT!', 16, 0)

    sleep(show_time)
    clean_lcd(lcd)
    clean_oled(oled)
