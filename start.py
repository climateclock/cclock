# Show the startup message as soon as possible.
import displayio
bitmap = displayio.Bitmap(192, 32, 16)

import display
display.BIT_DEPTH = 4  # save memory
display.init(bitmap)
title_pi = display.get_pi(0x00, 0xff, 0x00)
pi = display.get_pi(0x80, 0x80, 0x80)

import microfont
import utils
microfont.init()
microfont.small.draw('ClimateClock.world', bitmap, 1, 0, title_pi)
microfont.small.draw(f'Action Clock v{utils.version_num()}', bitmap, 1, 11, pi)
w = microfont.small.measure('#ActInTime')
microfont.small.draw('#ActInTime', bitmap, 192 - w, 0, pi)
display.send()

#IMPORTS#

import utils
utils.log()
import inputs
up, down, enter, brightness, selector, power_sensor = inputs.init()
utils.log('Initialized inputs')

utils.log()
import network
net = network.init()
utils.log('Initialized network')

import app
app.run(
    bitmap, net, power_sensor,
    {'UP': up, 'DOWN': down, 'ENTER': enter},
    {'BRIGHTNESS': brightness, 'SELECTOR': selector}
)
