import analogio
import digitalio
import board
import rotaryio


class PositionDial:
    def __init__(self, input):
        self.input = input

    @property
    def position(self):
        return self.input.value/65536.0


def init():
    up = digitalio.DigitalInOut(board.BUTTON_UP)
    up.pull = digitalio.Pull.UP
    down = digitalio.DigitalInOut(board.BUTTON_DOWN)
    down.pull = digitalio.Pull.UP
    enter = digitalio.DigitalInOut(board.A4)
    enter.pull = digitalio.Pull.UP
    brightness = PositionDial(analogio.AnalogIn(board.A1))
    selector = rotaryio.IncrementalEncoder(board.A2, board.A3)
    return up, down, enter, brightness, selector
