import board
import gpio
import neopixel
import storage
import supervisor

up = gpio.Button(board.BUTTON_UP)
down = gpio.Button(board.BUTTON_DOWN)

# By default, the filesystem is writable from Python to let the software update
# itself.  Hold either button on boot to make the filesystem writable over USB.
production_mode = not(up.pressed or down.pressed)
if production_mode:
    storage.remount('/', readonly=False)
    supervisor.disable_autoreload()

neopixel.NeoPixel(board.NEOPIXEL, 1).fill(
    (6, 0, 24) if production_mode  # PuRple means PRoduction mode
    else (24, 0, 0)  # Red means you can wRite
)

up.deinit()
down.deinit()
