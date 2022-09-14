# Show the startup message as soon as possible.
import microfont
import sys
microfont.set_dirs(sys.path[0], '/')
import prefs
prefs.init()
import matrix_frame
display_frame = matrix_frame.new_display_frame(
    192, 32, 16, prefs.get('rgb_pins'), prefs.get('addr_pins'))
ver = sys.path[0].split('.')[0]
title_cv = display_frame.pack(0x00, 0xff, 0x00)
text_cv = display_frame.pack(0x80, 0x80, 0x80)
display_frame.print(1, 0, 'ClimateClock.world', 'kairon-10', cv=title_cv)
display_frame.print(1, 11, f'Action Clock {ver}', 'kairon-10', cv=text_cv)
display_frame.print(1, 22, '#ActInTime', 'kairon-10', cv=text_cv)
display_frame.send()

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
import esp_wifi_network
network = esp_wifi_network.EspWifiNetwork()
utils.log('Created EspWifiNetwork')

import app
app.run(
    network,
    display_frame,
    {'UP': up, 'DOWN': down, 'ENTER': enter},
    {'BRIGHTNESS': brightness, 'SELECTOR': selector}
)
