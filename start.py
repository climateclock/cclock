# Show the startup message as soon as possible.
import displayio
bitmap = displayio.Bitmap(192, 32, 16)

import display
display.init(bitmap)
title_pi = display.get_pi(0x00, 0xff, 0x00)
text_pi = display.get_pi(0x80, 0x80, 0x80)

import microfont
import sys
microfont.init()
ver = sys.path[0].split('.')[0].split('-')[0]
microfont.small.draw('ClimateClock.world', bitmap, 1, 0, title_pi)
microfont.small.draw(f'Action Clock {ver}', bitmap, 1, 11, text_pi)
microfont.small.draw('#ActInTime', bitmap, 1, 22, text_pi)
display.send()

#IMPORTS#

import utils
utils.log()
import inputs
up, down, enter, brightness, selector = inputs.init()
utils.log('Initialized inputs')

utils.log()
import network
net = network.init()
utils.log('Initialized network')

import app
app.run(
    bitmap, net,
    {'UP': up, 'DOWN': down, 'ENTER': enter},
    {'BRIGHTNESS': brightness, 'SELECTOR': selector}
)
