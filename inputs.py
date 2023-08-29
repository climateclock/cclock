import analogio
import board
import digitalio
import rotaryio


class PositionDial:
    def __init__(self, input):
        self.input = input

    @property
    def position(self):
        return self.input.value/65536.0


class PowerSensor:
    def __init__(self, pin=None):
        self.analog = pin and analogio.AnalogIn(pin)

    @property
    def level(self):  # returns a battery percentage level from 0 to 100
        if not self.analog:
            return 50  # no battery reading available
        fraction = (self.analog.value - 40000) / 8000  # roughly 40000 to 48000
        return max(0, min(100, int(fraction * 100)))


def init():
    hw_revision = 0
    i2c = board.I2C()
    try:
        while not i2c.try_lock():
            pass
        if 0x20 in i2c.scan():  # main board has a PCF8574 on I2C device 0x20
            rev_code = bytearray(1)
            i2c.readfrom_into(0x20, rev_code)
            hw_revision = ((~rev_code[0] >> 4) & 0xf) + 1
    finally:
        i2c.unlock()
    print('Detected hardware revision:', hw_revision)

    up = digitalio.DigitalInOut(board.BUTTON_UP)
    up.pull = digitalio.Pull.UP
    down = digitalio.DigitalInOut(board.BUTTON_DOWN)
    down.pull = digitalio.Pull.UP
    enter = digitalio.DigitalInOut(board.A4 if hw_revision == 0 else board.TX)
    enter.pull = digitalio.Pull.UP
    brightness = PositionDial(analogio.AnalogIn(board.A1))
    selector = rotaryio.IncrementalEncoder(board.A2, board.A3)
    power_sensor = PowerSensor(None if hw_revision == 0 else board.A4)
    return up, down, enter, brightness, selector, power_sensor
