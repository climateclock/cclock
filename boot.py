import board
import digitalio
import neopixel
import storage
import supervisor

up = digitalio.DigitalInOut(board.BUTTON_UP)
down = digitalio.DigitalInOut(board.BUTTON_DOWN)

# By default, the filesystem is writable from Python to let the software update
# itself.  Hold either button on boot to make the filesystem writable over USB.
production_mode = up.value and down.value  # buttons are normally high (True)
if production_mode:
    storage.remount('/', readonly=False)
    supervisor.disable_autoreload()

neopixel.NeoPixel(board.NEOPIXEL, 1).fill(
    (6, 0, 24) if production_mode  # PuRple means PRoduction mode
    else (24, 0, 0)  # Red means you can wRite
)

up.deinit()
down.deinit()
