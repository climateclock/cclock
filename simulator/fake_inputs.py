import inputs
import os
from sdl2 import *

pressed_scancodes = set()
key_handlers = []


def install():
    inputs.init = init


def init():
    up = FakeButton('UP', SDL_SCANCODE_LSHIFT)
    down = FakeButton('DOWN', SDL_SCANCODE_RSHIFT)
    enter = FakeButton('ENTER', SDL_SCANCODE_RETURN)
    brightness = FakeDial(
        'BRIGHTNESS', SDL_SCANCODE_DOWN, SDL_SCANCODE_UP, 1/8, 1.0, 0.0, 1.0)
    selector = FakeDial(
        'SELECTOR', SDL_SCANCODE_LEFT, SDL_SCANCODE_RIGHT, 1, 0, -10000, 10000)
    battery_sensor = FakeBatterySensor(
        'BATTERY', SDL_SCANCODE_COMMA, SDL_SCANCODE_PERIOD, 4, 70, 0, 100)
    return up, down, enter, brightness, selector, battery_sensor


def handle_event(event):
    scancode = event.key.keysym.scancode
    if event.type == SDL_KEYDOWN:
        pressed_scancodes.add(scancode)
        for handler in key_handlers:
            handler.key_down(scancode)
    if event.type == SDL_KEYUP:
        pressed_scancodes.remove(scancode)


class FakeButton:
    def __init__(self, name, scancode):
        self.name = name
        self.scancode = scancode

    @property
    def value(self):
        # .value goes low when button is pressed
        return not (self.scancode in pressed_scancodes)


class FakeDial:
    def __init__(
        self, name, decr_scancode, incr_scancode, delta,
        position, min_position, max_position):
        key_handlers.append(self)
        self.name = name
        self.decr_scancode = decr_scancode
        self.incr_scancode = incr_scancode
        self.delta = delta
        self.position = position
        self.min_position = min_position
        self.max_position = max_position

    def key_down(self, scancode):
        if scancode == self.decr_scancode:
            self.position = max(self.min_position, self.position - self.delta)
            print(f'Simulator: {self.name} at {self.position}')
        if scancode == self.incr_scancode:
            self.position = min(self.max_position, self.position + self.delta)
            print(f'Simulator: {self.name} at {self.position}')


class FakeBatterySensor(FakeDial):
    @property
    def level(self):
        if os.environ.get('CCLOCK_DISABLE_BATTERY_SENSOR'):
            return None
        return self.position
