import sys
from fs import FileSystem
fs = FileSystem('/')
from prefs import Prefs
prefs = Prefs(fs)
from fontlib import FontLibrary
fontlib = FontLibrary(fs, [sys.path[0], '/'])

import matrix_frame
frame = matrix_frame.new_display_frame(
    192, 32, 16, fontlib, prefs.get('rgb_pins'), prefs.get('addr_pins'))

import board, gpio
up = gpio.Button(board.BUTTON_UP)
down = gpio.Button(board.BUTTON_DOWN)
enter = gpio.Button(board.A4)
brightness = gpio.AnalogInput(board.A1)
selector = gpio.RotaryInput(board.A2, board.A3)

from esp_wifi_network import EspWifiNetwork
network = EspWifiNetwork()

from app import run
run(
    prefs,
    network,
    frame,
    fs,
    {'UP': up, 'DOWN': down, 'ENTER': enter},
    {'BRIGHTNESS': brightness, 'SELECTOR': selector}
)

