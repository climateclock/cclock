from digitalio import DigitalInOut, Direction, Pull

def input(pin, default=None):
    io = DigitalInOut(pin)
    io.direction = Direction.INPUT
    io.pull = {True: Pull.UP, False: Pull.DOWN, None: None}[default]
    return io

def output(pin):
    io = DigitalInOut(pin)
    io.direction = Direction.OUTPUT
    return io
