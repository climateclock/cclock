from digitalio import DigitalInOut, Direction, Pull

def input(pin, default=None):
    input = DigitalInOut(pin)
    input.direction = Direction.INPUT
    input.pull = {True: Pull.UP, False: Pull.DOWN, None: None}[default]

def output(pin):
    output = DigitalInOut(pin)
    output.direction = Direction.OUTPUT
