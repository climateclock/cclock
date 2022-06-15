import board
import gpio
import neopixel
import storage

up = gpio.Button(board.BUTTON_UP)
down = gpio.Button(board.BUTTON_DOWN)

# By default, the filesystem is writable from Python to let the software update
# itself.  Hold either button on boot to make the filesystem writable over USB.
usb_write_enabled = up.pressed or down.pressed
storage.remount('/', readonly=usb_write_enabled)
neopixel.NeoPixel(board.NEOPIXEL, 1).fill(
    (9, 9, 9) if usb_write_enabled  # WhITE means you can WrITE
    else (6, 0, 24)  # PuRple means PRoduction mode
)

up.deinit()
down.deinit()
