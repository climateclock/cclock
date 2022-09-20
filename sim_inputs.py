import inputs
from sdl2 import *

pressed_scancodes = set()
key_handlers = []


def install():
    inputs.init = init


def init():
    up = SimButton(SDL_SCANCODE_LSHIFT)
    down = SimButton(SDL_SCANCODE_RSHIFT)
    enter = SimButton(SDL_SCANCODE_RETURN)
    brightness = SimDial(
        SDL_SCANCODE_DOWN, SDL_SCANCODE_UP, 1/8.0, 1.0, 0.0, 1.0)
    selector = SimDial(
        SDL_SCANCODE_LEFT, SDL_SCANCODE_RIGHT, 1, 0, -100000, 100000)
    return up, down, enter, brightness, selector


def handle_event(event):
    scancode = event.key.keysym.scancode
    if event.type == SDL_KEYDOWN:
        pressed_scancodes.add(scancode)
        for handler in key_handlers:
            handler.key_down(scancode)
    if event.type == SDL_KEYUP:
        pressed_scancodes.remove(scancode)


class SimButton:
    def __init__(self, scancode):
        self.scancode = scancode

    @property
    def value(self):
        # .value goes low when button is pressed
        return not (self.scancode in pressed_scancodes)


class SimDial:
    def __init__(
        self, decr_scancode, incr_scancode, delta,
        position, min_position, max_position):
        key_handlers.append(self)
        self.decr_scancode = decr_scancode
        self.incr_scancode = incr_scancode
        self.delta = delta
        self.position = position
        self.min_position = min_position
        self.max_position = max_position

    def key_down(self, scancode):
        if scancode == self.decr_scancode:
            self.position = max(self.min_position, self.position - self.delta)
        if scancode == self.incr_scancode:
            self.position = min(self.max_position, self.position + self.delta)
