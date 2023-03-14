from lcd2004 import LCD
from ssd1306 import SSD1306_SPI
from machine import Pin, SoftSPI
from time import sleep

def display_lcd(addr=39, scl=12, sda=13):
    lcd = LCD(addr, scl, sda)
    lcd.lcd_backlight(True)
    lcd.lcd_print("Happy Wife,", 1, 0)
    lcd.lcd_print("Happy Life!", 2, 0)
    return lcd

def display_oled(width=128, height=64, res=21, dc=22, cs=23, sck=18, mosi=19, miso=15):
    spi = SoftSPI(baudrate=500000, polarity=1, phase=0, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
    res_pin = Pin(res)
    dc_pin = Pin(dc)
    cs_pin = Pin(cs)
    oled = SSD1306_SPI(width, height, spi, dc_pin, res_pin, cs_pin)
    oled.fill(0)
    oled.text('Wife is always', 0, 0)
    oled.text('RIGHT!', 0, 16)
    oled.show()
    return oled

def clean_lcd_display(lcd):
    lcd.lcd_clear()
    lcd.lcd_backlight(False)

def clean_oled_display(oled):
    oled.fill(0)
    oled.show()

def main(show_time=5):
    lcd = display_lcd()
    oled = display_oled()
    sleep(show_time)
    clean_lcd_display(lcd)
    clean_oled_display(oled)


if __name__ == '__main__':
    main(5)
