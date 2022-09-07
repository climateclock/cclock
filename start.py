import sys
from utils import log
import prefs
prefs.init()
import microfont
microfont.set_dirs(sys.path[0], '/')

log()
import matrix_frame
frame = matrix_frame.new_display_frame(
    192, 32, 16, prefs.get('rgb_pins'), prefs.get('addr_pins'))
log('Finished new_display_frame')

log()
import board, gpio
up = gpio.Button(board.BUTTON_UP)
down = gpio.Button(board.BUTTON_DOWN)
enter = gpio.Button(board.A4)
brightness = gpio.AnalogInput(board.A1)
selector = gpio.RotaryInput(board.A2, board.A3)
log('Created gpio objects')

log()
from esp_wifi_network import EspWifiNetwork
network = EspWifiNetwork()
log('Created EspWifiNetwork')

from app import run
run(
    network,
    frame,
    {'UP': up, 'DOWN': down, 'ENTER': enter},
    {'BRIGHTNESS': brightness, 'SELECTOR': selector}
)
