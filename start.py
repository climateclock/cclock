# Show the startup message as soon as possible.
import displayio
bitmap = displayio.Bitmap(192, 32, 16)

import display
display.init(bitmap)
title_pi = display.get_pi(0x00, 0xff, 0x00)
text_pi = display.get_pi(0x80, 0x80, 0x80)

import microfont
import sys
microfont.init(sys.path[0], '/')
ver = sys.path[0].split('.')[0]
microfont.small.draw('ClimateClock.world', bitmap, 1, 0, title_pi)
microfont.small.draw(f'Action Clock {ver}', bitmap, 1, 11, text_pi)
microfont.small.draw('#ActInTime', bitmap, 1, 22, text_pi)
display.send()

#IMPORTS#

utils.log()
import gpio
up = gpio.Button(board.BUTTON_UP)
down = gpio.Button(board.BUTTON_DOWN)
enter = gpio.Button(board.A4)
brightness = gpio.AnalogInput(board.A1)
selector = gpio.RotaryInput(board.A2, board.A3)
utils.log('Created gpio objects')

utils.log()
import esp
esp_spi = esp.init_esp()
utils.log('Initialized ESP')
from adafruit_esp32spi import adafruit_esp32spi_socket as socklib

import app
app.run(
    bitmap,
    esp_spi,
    socklib,
    {'UP': up, 'DOWN': down, 'ENTER': enter},
    {'BRIGHTNESS': brightness, 'SELECTOR': selector}
)
