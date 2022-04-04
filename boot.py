import board
from digitalio import DigitalInOut, Direction, Pull
import storage

up = DigitalInOut(board.BUTTON_UP)
up.direction = Direction.INPUT
up.pull = Pull.UP

down = DigitalInOut(board.BUTTON_DOWN)
down.direction = Direction.INPUT
down.pull = Pull.UP

# By default, the filesystem is writable from Python to let the software update
# itself.  Hold either button on boot to make the filesystem writable over USB.
pressed = (not up.value) or (not down.value)
storage.remount('/', readonly=pressed)
