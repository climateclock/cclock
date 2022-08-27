import sys
import utils

from prefs import Prefs
prefs = Prefs()
utils.mem('Prefs')
from fontlib import FontLibrary
fontlib = FontLibrary([sys.path[0], '/'])
utils.mem('FontLibrary')

import matrix_frame
frame = matrix_frame.new_display_frame(
    192, 32, 16, fontlib, prefs.get('rgb_pins'), prefs.get('addr_pins'))
utils.mem('new_display_frame')

import board, gpio
up = gpio.Button(board.BUTTON_UP)
down = gpio.Button(board.BUTTON_DOWN)
enter = gpio.Button(board.A4)
brightness = gpio.AnalogInput(board.A1)
selector = gpio.RotaryInput(board.A2, board.A3)
utils.mem('pins')

from esp_wifi_network import EspWifiNetwork
network = EspWifiNetwork()
utils.mem('EspWifiNetwork')

from app import run
utils.mem('pre-run')
run(
    prefs,
    network,
    frame,
    {'UP': up, 'DOWN': down, 'ENTER': enter},
    {'BRIGHTNESS': brightness, 'SELECTOR': selector}
)
