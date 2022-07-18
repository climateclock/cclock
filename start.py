import sys
import utils

utils.mem('start1')
from fs import FileSystem
fs = FileSystem('/')
utils.mem('start2')
from fontlib import FontLibrary
fontlib = FontLibrary(fs, [sys.path[0], '/'])
utils.mem('start3')

import matrix_frame
utils.mem('start4')
frame = matrix_frame.new_display_frame(192, 32, 16, fontlib)
utils.mem('start5')

import board, gpio
utils.mem('start5')
up = gpio.Button(board.BUTTON_UP)
down = gpio.Button(board.BUTTON_DOWN)
enter = gpio.Button(board.A4)
brightness = gpio.AnalogInput(board.A1)
selector = gpio.RotaryInput(board.A2, board.A3)
utils.mem('start6')

from esp_wifi_network import EspWifiNetwork
utils.mem('start7')
network = EspWifiNetwork()
utils.mem('start8')

from app import run
utils.mem('start9')
run(
    fs,
    network,
    frame,
    {'UP': up, 'DOWN': down, 'ENTER': enter},
    {'BRIGHTNESS': brightness, 'SELECTOR': selector}
)

