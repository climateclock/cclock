import board
import gpio
import storage

up = gpio.Button(board.BUTTON_UP)
down = gpio.Button(board.BUTTON_DOWN)

# By default, the filesystem is writable from Python to let the software update
# itself.  Hold either button on boot to make the filesystem writable over USB.
storage.remount('/', readonly=up.pressed or down.pressed)

up.deinit()
down.deinit()
