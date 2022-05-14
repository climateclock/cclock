import board
import gpio
import storage

up = gpio.input(board.BUTTON_UP, default=True)
down = gpio.input(board.BUTTON_DOWN, default=True)

# By default, the filesystem is writable from Python to let the software update
# itself.  Hold either button on boot to make the filesystem writable over USB.
pressed = (not up.value) or (not down.value)
storage.remount('/', readonly=pressed)
